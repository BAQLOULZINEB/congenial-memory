from time import perf_counter

import httpx
import numpy as np

from backend.config import settings
from backend.embeddings import get_embedder
from backend.extraction import extract
from backend.parsing import clean_text
from backend.recommendations import generate, local_recommendations
from backend.schemas import AnalysisRequest, AnalysisResult, Component, Gap
from backend.taxonomy import HARD, RELATED


def analyze(request: AnalysisRequest, embedder=None) -> AnalysisResult:
    started = perf_counter()
    cv = extract(clean_text(request.cv_text))
    job = extract(clean_text(request.job_text), is_job=True)
    parsed = perf_counter()
    warnings = ["Le score est une aide à la lecture, pas une décision de recrutement.",
                "L'extraction utilise un dictionnaire spaCy : les compétences hors vocabulaire peuvent être omises."]
    if not job.skills:
        raise ValueError("Aucune compétence reconnue dans l'offre. Ajoutez des exigences techniques explicites.")
    engine = embedder or get_embedder()
    cv_skills = cv.skills
    descriptions = [f"{s.name}: {s.evidence}" for s in job.skills + cv_skills]
    vectors = engine.encode(descriptions)
    similarities = vectors[:len(job.skills)] @ vectors[len(job.skills):].T
    gaps = []
    for i, required in enumerate(job.skills):
        exact = next((s for s in cv_skills if s.name == required.name), None)
        if exact:
            gaps.append(Gap(skill=required.name, category=required.category, status="Couvert", similarity=1,
                            evidence=exact.evidence, required=required.required))
            continue
        candidates = []
        for j, candidate in enumerate(cv_skills):
            same_domain = (required.name in HARD and candidate.name in HARD and
                           HARD[required.name][1] == HARD[candidate.name][1])
            related = candidate.name in RELATED.get(required.name, set())
            similarity = float(np.clip(similarities[i, j], 0, 1))
            if related or (same_domain and similarity >= 0.60):
                candidates.append((max(similarity, 0.60) if related else similarity, candidate))
        best = max(candidates, key=lambda c: c[0]) if candidates else None
        gaps.append(Gap(skill=required.name, category=required.category, status="Partiel" if best else "Absent",
                        similarity=round(best[0], 4) if best else 0,
                        evidence=f"Compétence connexe : {best[1].name}. {best[1].evidence}" if best else "Aucune preuve reconnue dans le CV.",
                        required=required.required))
    components = {}
    for category in ("hard_skills", "soft_skills"):
        relevant = [g for g in gaps if g.category == category]
        denominator = sum(1 if g.required else 0.5 for g in relevant)
        value = sum((1 if g.required else 0.5) * (100 if g.status == "Couvert" else
                    50 * g.similarity if g.status == "Partiel" else 0) for g in relevant)
        components[category] = Component(score=round(value / denominator, 2) if denominator else None,
                                          explanation="Preuves exactes : 100 ; proximité sémantique : 50 × cosinus ; absence : 0. "
                                          "Les exigences souhaitables comptent pour moitié.")
    for key, actual, expected in [("experience", cv.experience_years, job.experience_years),
                                  ("education", cv.education_level, job.education_level)]:
        if expected is None:
            components[key] = Component(score=None, explanation="Aucune exigence explicite reconnue dans l'offre.")
        elif actual is None:
            components[key] = Component(score=0, explanation="Exigence présente, mais preuve non identifiée dans le CV.")
            warnings.append(f"{'Expérience' if key == 'experience' else 'Formation'} non identifiée : vérifier manuellement.")
        else:
            components[key] = Component(score=round(min(actual / expected, 1) * 100, 2) if expected else 100,
                                          explanation=f"CV : {actual:g} ; offre : {expected:g}. " +
                                          ("Années déclarées explicitement, dates non cumulées." if key == "experience" else
                                           "Niveau académique uniquement ; spécialité et équivalences à vérifier."))
    weights = request.weights.model_dump()
    available = sum(weights[k] for k, v in components.items() if v.score is not None)
    if available <= 0:
        raise ValueError("Les critères détectés ont tous un poids nul. Ajustez les pondérations.")
    effective = {k: weights[k] / available if v.score is not None else 0 for k, v in components.items()}
    score = round(sum((v.score or 0) * effective[k] for k, v in components.items()), 1)
    if any(v.score is None for v in components.values()):
        warnings.append("Les critères non exigés sont exclus ; les poids restants sont renormalisés.")
    scored = perf_counter()
    recommendations = local_recommendations(gaps, score)
    if request.use_llm:
        try:
            recommendations = generate(recommendations, gaps)
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            warnings.append("Le service de génération est indisponible ou sa réponse invalide. Conseils locaux affichés.")
    finished = perf_counter()
    return AnalysisResult(score=score, weights=request.weights, effective_weights=effective, components=components,
                          gaps=gaps, cv=cv, job=job, recommendations=recommendations, warnings=warnings,
                          timings_ms={"extraction": round((parsed-started)*1000, 1),
                                      "matching": round((scored-parsed)*1000, 1),
                                      "recommendations": round((finished-scored)*1000, 1),
                                      "total": round((finished-started)*1000, 1)},
                          embedding_model=settings().embedding_model)


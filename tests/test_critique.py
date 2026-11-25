"""Phase « Guider » : critical review and guards on generated text."""
import numpy as np

from backend.analysis import analyze
from backend.recommendations import _guard
from backend.schemas import AnalysisRequest, Critique, Recommendations, Rewrite


class FakeEmbedder:
    def encode(self, texts):
        return np.eye(len(texts))


CV = """Profil
Zineb Test, zineb@example.test
Compétences
Python, scikit-learn, SQL, Git
Expériences professionnelles
Développement d'un modèle de classification avec scikit-learn pour trier des tickets.
Formation
Cycle ingénieur en data science (Bac+5)."""

JOB = """Data Scientist
Compétences obligatoires : Python, apprentissage supervisé, Docker, AWS.
2 ans d'expérience professionnelle. Master requis. Autonomie."""


def run():
    return analyze(AnalysisRequest(cv_text=CV, job_text=JOB, use_llm=False), FakeEmbedder())


def test_synonym_concept_is_covered_through_tool():
    gaps = {g.skill: g for g in run().gaps}
    assert gaps["Machine Learning"].status == "Couvert"
    assert gaps["Machine Learning"].via == "scikit-learn"
    assert gaps["Machine Learning"].term == "apprentissage supervisé"


def test_optional_marker_only_applies_to_its_own_sentence():
    gaps = {g.skill: g for g in analyze(AnalysisRequest(
        cv_text=CV, job_text="Data Scientist. Python requis.\nAutonomie exigée. AWS est un atout.", use_llm=False),
        FakeEmbedder()).gaps}
    assert gaps["Autonomie"].required is True
    assert gaps["AWS"].required is False


def test_local_review_is_critical():
    rec = run().recommendations
    assert rec.verdict == "Non recommandée en l'état"  # 2 of 4 required hard skills absent
    blocking = [c.point for c in rec.critique if c.severity == "bloquant"]
    assert any("Docker" in p for p in blocking) and any("AWS" in p for p in blocking)
    assert any("apprentissage supervisé" in c.point for c in rec.critique)  # offer wording missing from CV
    assert any("chiffré" in c.point for c in rec.critique)
    assert rec.critique == sorted(rec.critique, key=lambda c: ["bloquant", "majeur", "mineur"].index(c.severity))
    assert rec.summary.startswith("Verdict : ")
    assert any("apprentissage supervisé" in r.suggestion for r in rec.rewrites)


def test_guard_rejects_lenient_verdict_fabricated_rewrites_and_dropped_blockers():
    result = run()
    base = result.recommendations
    generated = Recommendations(
        summary="Très bon profil.", strengths=[], priorities=[], source="llm", verdict="Solide",
        verdict_rationale="", critique=[Critique(severity="mineur", point="Style", explanation="RAS")],
        rewrites=[Rewrite(original="A dirigé une équipe de 12 personnes", suggestion="Dirigé 12 personnes"),
                  Rewrite(original="Développement d'un modèle de classification avec scikit-learn pour trier des tickets.",
                          suggestion="Conçu un modèle d'apprentissage supervisé triant 95 % des tickets"),
                  Rewrite(original="Développement d'un modèle de classification avec scikit-learn pour trier des tickets.",
                          suggestion="Conçu un modèle d'apprentissage supervisé (scikit-learn) pour trier les tickets "
                                     "[volume à préciser]")],
        actions=[])
    guarded = _guard(generated, base, result.gaps, "\n".join(v for k, v in result.cv.sections.items() if k != "profile"))
    assert guarded.verdict == base.verdict  # never more favourable than the rules
    assert len(guarded.rewrites) == 1 and "[volume à préciser]" in guarded.rewrites[0].suggestion
    assert {"Docker", "AWS"} <= {c.point.split(" : ")[-1] for c in guarded.critique if c.severity == "bloquant"}
    assert guarded.actions  # fell back to rule-based actions
    assert guarded.source == "llm"


def test_guard_accepts_stricter_verdict():
    result = run()
    base = result.recommendations.model_copy(update={"verdict": "Recevable avec réserves"})
    generated = base.model_copy(update={"verdict": "Fragile", "source": "llm"})
    assert _guard(generated, base, result.gaps, "").verdict == "Fragile"


def test_old_saved_results_without_critique_still_validate():
    legacy = {"summary": "x", "strengths": [], "priorities": [], "rewrites": [{"original": "a", "suggestion": "b"}],
              "actions": [], "source": "local"}
    rec = Recommendations.model_validate(legacy)
    assert rec.verdict is None and rec.critique == []

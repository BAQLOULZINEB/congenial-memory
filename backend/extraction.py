import re
import unicodedata
from functools import lru_cache

import spacy

from backend.schemas import Profile, Skill
from backend.taxonomy import HARD, SOFT


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


@lru_cache
def nlp():
    pipeline = spacy.blank("fr")
    ruler = pipeline.add_pipe("entity_ruler", config={"phrase_matcher_attr": "LOWER"})
    patterns = []
    for name, (aliases, _, _) in HARD.items():
        patterns.extend({"label": "HARD", "pattern": alias, "id": name} for alias in aliases)
    for name, aliases in SOFT.items():
        patterns.extend({"label": "SOFT", "pattern": alias, "id": name} for alias in aliases)
    ruler.add_patterns(patterns)
    return pipeline


HEADINGS = {
    "experience": r"^(experiences?( professionnelles?)?|professional experience|work experience|employment)\s*:?$",
    "education": r"^(formations?( academiques?)?|education|cursus( academique)?|diplomes?)\s*:?$",
    "skills": r"^(competences?( techniques?)?|technical skills|skills|technologies|boite a outils( techniques)?)\s*:?$",
    "projects": r"^(projets?( academiques?)?|projects|personal projects)\s*:?$",
}


def segment(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"profile": []}
    current = "profile"
    for line in text.splitlines():
        title = fold(line.strip().lstrip("# "))
        heading = next((key for key, pattern in HEADINGS.items() if re.match(pattern, title)), None)
        if heading:
            current = heading
            sections.setdefault(current, [])
        else:
            sections[current].append(line)
    return {key: "\n".join(value) for key, value in sections.items() if value}


def extract(text: str, is_job: bool = False) -> Profile:
    doc = nlp()(text)
    skills: dict[str, Skill] = {}
    for ent in doc.ents:
        start = max(text.rfind("\n", 0, ent.start_char), text.rfind(".", 0, ent.start_char)) + 1
        end = text.find("\n", ent.end_char)
        evidence = text[start:end if end >= 0 else len(text)].strip()[:400]
        prefix = fold(text[max(start, ent.start_char - 55):ent.start_char])
        if re.search(r"(?:sans|pas de|aucune?|no|not|without|ne maitrise pas)\s+(?:experience (?:en|with)\s+|connaissance (?:de|en)\s+)?$", prefix):
            continue
        optional = bool(re.search(r"souhait|apprecie|bonus|atout|ideale|preferred|nice.to.have|optional", fold(evidence)))
        skill = Skill(name=ent.ent_id_, category="hard_skills" if ent.label_ == "HARD" else "soft_skills",
                      evidence=evidence, required=not optional if is_job else True)
        if skill.name not in skills or skill.required:
            skills[skill.name] = skill
    years = []
    normalized = fold(text)
    for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*(?:a\s*\d+\s*)?\+?\s*(ans?|annees?|years?)\b", normalized):
        context = normalized[max(0, m.start() - 45):m.end() + 55]
        if re.search(r"experience|experiences|professionnel|worked|emploi", context):
            duration = float(m.group(1).replace(",", "."))
            if 0 <= duration <= 80:
                years.append(duration)
    # Explicit durations only: do not double-count overlapping jobs or invent years from graduation dates.
    degrees = []
    levels = []
    for pattern, level in [(r"\b(?:doctorat|ph\.?d|phd)\b", 8),
                           (r"\b(?:master|msc|ingenieur|engineering degree)\b|bac\s*\+\s*5", 5),
                           (r"\b(?:licence|bachelor|bsc)\b|bac\s*\+\s*3", 3),
                           (r"\b(?:bts|dut)\b|bac\s*\+\s*2", 2)]:
        for match in re.finditer(pattern, normalized):
            degrees.append(text[match.start():match.end()])
            levels.append(level)
    return Profile(sections=segment(text), skills=list(skills.values()),
                   experience_years=max(years) if years else None,
                   education_level=max(levels) if levels else None, degrees=list(dict.fromkeys(degrees)))


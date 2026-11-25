"""Conservative duration extraction; merge dated jobs instead of double-counting them."""
import re
from datetime import date

MONTHS = {
    "janvier": 1, "january": 1, "jan": 1, "fevrier": 2, "february": 2, "fev": 2, "feb": 2,
    "mars": 3, "march": 3, "mar": 3, "avril": 4, "april": 4, "avr": 4, "apr": 4,
    "mai": 5, "may": 5, "juin": 6, "june": 6, "jun": 6, "juillet": 7, "july": 7, "jul": 7,
    "aout": 8, "august": 8, "aug": 8, "septembre": 9, "september": 9, "sept": 9, "sep": 9,
    "octobre": 10, "october": 10, "oct": 10, "novembre": 11, "november": 11, "nov": 11,
    "decembre": 12, "december": 12, "dec": 12,
}
DATE = r"(?:(?:0?[1-9]|1[0-2])[/.-]|(?:" + "|".join(MONTHS) + r")\.?\s+)?(?:19|20)\d{2}"
PRESENT = r"(?:aujourd['’]hui|present|actuel(?:lement)?|en cours|current|now|today)"
PERIOD = re.compile(rf"(?<!\w)({DATE})\s*(?:[-–—]|\ba\b|\bau\b|\bto\b|\bjusqu['’]?a\b)\s*({DATE}|{PRESENT})(?!\w)")


def experience_years(text: str, sections: dict[str, str], is_job: bool = False, today: date | None = None):
    """Inputs are accent-folded. Explicit contextual totals take precedence over dates."""
    totals = []
    duration_pattern = r"(\d+(?:[.,]\d+)?)\s*(?:a\s*\d+\s*)?\+?\s*(ans?|annees?|years?|mois|months?)\b"
    experience_lines = sections.get("experience", "").splitlines()
    for line in text.splitlines():
        if not re.search(r"experience|professionnel|worked|emploi", line) and line not in experience_lines:
            continue
        matches = list(re.finditer(duration_pattern, line))
        for i, match in enumerate(matches):
            value = float(match[1].replace(",", "."))
            months = match[2] in ("mois", "month", "months")
            if months and i and re.fullmatch(r"\s*(?:et|and)?\s*", line[matches[i-1].end():match.start()]):
                continue  # Already included in the preceding years + months expression.
            if not months and i + 1 < len(matches):
                following = matches[i+1]
                if following[2] in ("mois", "month", "months") and re.fullmatch(
                    r"\s*(?:et|and)?\s*", line[match.end():following.start()]
                ):
                    value += float(following[1].replace(",", ".")) / 12
            elif months:
                value /= 12
            if 0 <= value <= 80:
                totals.append(value)
    if totals:
        return round(max(totals), 2)
    if is_job:
        return None  # Never turn offer publication dates into requirements.
    today = today or date.today()
    current = today.year * 12 + today.month - 1

    def month_index(token):
        if re.fullmatch(PRESENT, token):
            return current, True
        year = int(token[-4:])
        prefix = token[:-4].strip().rstrip("./-")
        month = int(prefix) if prefix.isdigit() else MONTHS.get(prefix, 1)
        return year * 12 + month - 1, bool(prefix)

    periods = []
    for match in PERIOD.finditer(sections.get("experience", "")):
        start, _ = month_index(match[1])
        end, precise = month_index(match[2])
        # Include the stated end month; bare years use the year difference conservatively.
        end = min(end + int(precise), current + 1)
        if start < end and 0 < end - start <= 80 * 12:
            periods.append((start, end))
    merged = []
    for start, end in sorted(periods):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return round(sum(end - start for start, end in merged) / 12, 2) if merged else None

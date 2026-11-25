from datetime import date

import pytest

from backend.experience import experience_years
from backend.extraction import extract, fold, segment


@pytest.mark.parametrize("text, expected", [
    ("Expérience professionnelle : 6 mois en Python.", 0.5),
    ("2 ans et 6 mois d'expérience professionnelle.", 2.5),
    ("18 months of professional experience with Python.", 1.5),
    ("Expérience professionnelle\n6 mois : développement Python.", 0.5),
    ("Expériences professionnelles\n01/2021 - 12/2022 : Python\n01/2022 - 12/2023 : SQL", 3),
    ("Expériences professionnelles\nJanvier 2021 - décembre 2022 : Python\nJanvier 2023 - décembre 2024 : SQL", 4),
    ("Expérience\n2020 - 2022 : Python\n2023 - 2024 : SQL", 3),
    ("Formation\n2020 - 2024 : Master informatique", None),
    ("Profil\n25 ans.\nExpérience\nDéveloppement Python", None),
    ("Expérience\n2024 - 2020 : Python", None),
    ("Profil\n5 ans d'expérience.\nExpérience\n2020 - 2022 : Python", 5),
])
def test_experience_formats(text, expected):
    assert extract(text).experience_years == expected


def test_current_period_and_offer_dates():
    text = "Expérience\njanvier 2026 - aujourd’hui : Python"
    assert experience_years(fold(text), {k: fold(v) for k, v in segment(text).items()},
                            today=date(2026, 6, 1)) == 0.5
    assert extract(text, is_job=True).experience_years is None

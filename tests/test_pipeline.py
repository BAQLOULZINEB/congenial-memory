import io
from pathlib import Path

import numpy as np
import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.analysis import analyze
from backend.extraction import extract
from backend.main import app
from backend.parsing import DocumentError, clean_text, extract_document
from backend.schemas import AnalysisRequest, Weights
from frontend.reports import gap_csv, html_report

ROOT = Path(__file__).resolve().parents[1]


class FakeEmbedder:
    def encode(self, texts):
        # Orthogonal embeddings prevent accidental semantic matches in deterministic tests.
        return np.eye(len(texts))


@pytest.fixture
def request_data():
    return AnalysisRequest(cv_text=(ROOT / "examples/cv.txt").read_text(encoding="utf-8"),
                           job_text=(ROOT / "examples/job.txt").read_text(encoding="utf-8"))


def test_weights_reject_invalid_totals_and_nonfinite_values():
    for kwargs in ({"hard_skills": 0.9}, {"experience": -1}, {"education": float("nan")}):
        with pytest.raises(ValidationError):
            Weights(**kwargs)


def test_normalization_boundaries_and_negation():
    profile = extract("Compétences\nPython3, sklearn, C++, C#, JavaScript.\nSans expérience en Docker.\nGitHub.")
    names = {s.name for s in profile.skills}
    assert {"Python", "scikit-learn", "C++", "C#", "JavaScript", "Git"} <= names
    assert "Docker" not in names
    assert "Java" not in names


def test_experience_education_and_sections():
    profile = extract("Profil\n3 ans d'expérience professionnelle.\nFormation\nMaster informatique\nProjets\nAPI Python")
    assert profile.experience_years == 3
    assert profile.education_level == 5
    assert "education" in profile.sections
    assert "projects" in profile.sections
    assert extract("J'ai 25 ans. Python pour mes projets.").experience_years is None


def test_explicit_match_related_skill_and_missing(request_data):
    result = analyze(request_data, FakeEmbedder())
    gaps = {g.skill: g for g in result.gaps}
    assert gaps["Python"].status == "Couvert"
    assert gaps["Machine Learning"].status == "Partiel"
    assert gaps["AWS"].status == "Absent"
    assert gaps["FastAPI"].required is False
    assert result.components["experience"].score == pytest.approx(66.67)
    assert result.score == pytest.approx(sum(result.effective_weights[k] * (v.score or 0)
                                            for k, v in result.components.items()), abs=0.05)


def test_missing_requirements_renormalize_not_free_points():
    result = analyze(AnalysisRequest(cv_text="Python et SQL pour mes projets personnels.",
                                    job_text="Compétences obligatoires : Python et Docker."), FakeEmbedder())
    assert result.effective_weights["hard_skills"] == 1
    assert result.score == 50
    assert result.components["education"].score is None


def test_unknown_cv_does_not_receive_semantic_credit():
    result = analyze(AnalysisRequest(cv_text="Je possède une formation en histoire de l'art.",
                                    job_text="Développement : Python et SQL sont obligatoires."), FakeEmbedder())
    assert result.score == 0
    assert all(g.status == "Absent" for g in result.gaps)


def test_no_detected_job_skills_is_clear_error():
    with pytest.raises(ValueError, match="Aucune compétence"):
        analyze(AnalysisRequest(cv_text="Python et SQL pour mes projets personnels.",
                                job_text="Nous recrutons un jardinier pour notre équipe."), FakeEmbedder())


def test_pdf_and_docx_roundtrip():
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((50, 50), "Python, SQL, Docker. Experience professionnelle : 3 ans.")
        pdf = document.tobytes()
    assert "Python" in extract_document("cv.pdf", pdf)
    document = Document()
    document.add_paragraph("Profil : developpeur Python avec experience professionnelle.")
    document.add_table(rows=1, cols=1).cell(0, 0).text = "Docker et SQL"
    stream = io.BytesIO()
    document.save(stream)
    assert "Docker et SQL" in extract_document("cv.docx", stream.getvalue())


@pytest.mark.parametrize("name,data", [("cv.txt", b"x" * 40), ("cv.pdf", b"broken"), ("cv.docx", b"broken"),
                                       ("cv.pdf", b"x" * (5 * 1024 * 1024 + 1))])
def test_invalid_files(name, data):
    with pytest.raises(DocumentError):
        extract_document(name, data)


def test_scanned_pdf_error():
    with pymupdf.open() as document:
        document.new_page()
        data = document.tobytes()
    with pytest.raises(DocumentError, match="OCR"):
        extract_document("scan.pdf", data)


def test_cleaning():
    assert clean_text("Python\x00  SQL\n\nDévelop-\npement") == "Python SQL\nDéveloppement"


def test_api_json_form_and_validation(monkeypatch, request_data):
    monkeypatch.setattr("backend.analysis.get_embedder", lambda: FakeEmbedder())
    # No lifespan: unit API tests deliberately avoid model downloads.
    client = TestClient(app)
    response = client.post("/api/analyze", json=request_data.model_dump())
    assert response.status_code == 200
    assert "gaps" in response.json()
    response = client.post("/api/analyze", json={"cv_text": "private-short", "job_text": "private-short"})
    assert response.status_code == 422
    assert "private-short" not in response.text
    response = client.post("/api/analyze/files", data={"cv_text": request_data.cv_text, "job_text": request_data.job_text})
    assert response.status_code == 200
    response = client.post("/api/analyze/files", data={"cv_text": "short", "job_text": "short"})
    assert response.status_code == 422
    assert "short" not in response.text
    response = client.post("/api/analyze/files", files={"cv_file": ("bad.pdf", b"broken", "application/pdf")},
                           data={"job_text": request_data.job_text})
    assert response.status_code == 422


def test_llm_failure_falls_back_visibly(monkeypatch, request_data):
    def fail(*args):
        raise ValueError("invalid model response")
    monkeypatch.setattr("backend.analysis.generate", fail)
    request_data.use_llm = True
    result = analyze(request_data, FakeEmbedder())
    assert result.recommendations.source == "local"
    assert any("indisponible" in warning for warning in result.warnings)


def test_exports_escape_untrusted_content(request_data):
    result = analyze(request_data, FakeEmbedder()).model_dump()
    result["gaps"][0]["evidence"] = '<script>alert(1)</script>'
    report = html_report(result)
    assert "<script>" not in report
    assert "&lt;script&gt;" in report
    result["gaps"][0]["evidence"] = '=HYPERLINK("evil")'
    assert "'=HYPERLINK" in gap_csv(result)


"""User-facing API contracts retained by the React migration."""
import io
import json

import numpy as np
import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas import AnalysisResult

CV_TEXT = "Profil : Python et SQL. Experience professionnelle : 3 ans. Master informatique."
JOB_TEXT = "Python et Docker obligatoires. Master informatique et 2 ans d'experience professionnelle."


class DeterministicEmbedder:
    def encode(self, texts):
        return np.eye(len(texts))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr("backend.analysis.get_embedder", lambda: DeterministicEmbedder())
    return TestClient(app)


def pdf_bytes(text):
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_textbox((40, 40, 550, 700), text)
        return document.tobytes()


def docx_bytes(text):
    document = Document()
    document.add_paragraph(text)
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


@pytest.mark.parametrize("cv_kind,job_kind", [("pdf", "docx"), ("docx", "pdf")])
def test_real_document_uploads_return_typed_analysis(client, cv_kind, job_kind):
    encoders = {"pdf": pdf_bytes, "docx": docx_bytes}
    response = client.post("/api/analyze/files", files={
        "cv_file": (f"cv.{cv_kind}", encoders[cv_kind](CV_TEXT)),
        "job_file": (f"offre.{job_kind}", encoders[job_kind](JOB_TEXT)),
    })
    assert response.status_code == 200, response.text
    result = AnalysisResult.model_validate(response.json())
    gaps = {gap.skill: gap.status for gap in result.gaps}
    assert gaps == {"Python": "Couvert", "Docker": "Absent"}
    assert result.recommendations.source == "local"
    assert result.components["education"].score == 100


@pytest.mark.parametrize("file_field,text_field,other_field", [
    ("cv_file", "cv_text", "job_text"), ("job_file", "job_text", "cv_text"),
])
def test_file_and_text_conflicts_are_rejected(client, file_field, text_field, other_field):
    response = client.post("/api/analyze/files", files={file_field: ("document.pdf", pdf_bytes(CV_TEXT))},
                           data={text_field: CV_TEXT, other_field: JOB_TEXT})
    assert response.status_code == 422
    assert "pas les deux" in response.json()["detail"]


@pytest.mark.parametrize("weights", ["not-json", '{"hard_skills":0.9}', '{"hard_skills":-1}',
                                   '{"unknown":0.5}', '{"hard_skills":NaN}'])
def test_invalid_multipart_weights_fail_without_returning_cv(client, weights):
    private_cv = CV_TEXT + " PRIVATE-CONTACT-MARKER"
    response = client.post("/api/analyze/files", data={"cv_text": private_cv, "job_text": JOB_TEXT,
                                                       "weights": weights})
    assert response.status_code == 422
    assert "PRIVATE-CONTACT-MARKER" not in response.text


def test_configurable_weights_are_honored_in_form_contract(client):
    weights = {"hard_skills": 1, "experience": 0, "education": 0, "soft_skills": 0}
    response = client.post("/api/analyze/files", data={"cv_text": CV_TEXT, "job_text": JOB_TEXT,
                                                       "weights": json.dumps(weights)})
    assert response.status_code == 200
    assert response.json()["score"] == 50
    assert response.json()["effective_weights"]["hard_skills"] == 1


def test_llm_disabled_never_calls_external_generator(client, monkeypatch):
    def forbidden_call(*args):
        pytest.fail("The default analysis must not transmit evidence to a language model service")
    monkeypatch.setattr("backend.analysis.generate", forbidden_call)
    response = client.post("/api/analyze/files", data={"cv_text": CV_TEXT, "job_text": JOB_TEXT,
                                                       "use_llm": "false"})
    assert response.status_code == 200
    assert response.json()["recommendations"]["source"] == "local"


def test_explicit_llm_failure_returns_local_result_with_warning(client, monkeypatch):
    def unavailable(*args):
        raise ValueError("invalid service response")
    monkeypatch.setattr("backend.analysis.generate", unavailable)
    monkeypatch.setattr("backend.analysis.llm_configured", lambda: True)
    response = client.post("/api/analyze/files", data={"cv_text": CV_TEXT, "job_text": JOB_TEXT,
                                                       "use_llm": "true"})
    assert response.status_code == 200
    assert response.json()["recommendations"]["source"] == "local"
    assert any("indisponible" in warning for warning in response.json()["warnings"])

import sqlite3
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import storage
from backend.analysis import analyze
from backend.main import app
from backend.schemas import AnalysisRequest


@pytest.fixture
def store_client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "database_path", lambda: tmp_path / "reports.sqlite3")
    storage.initialize()
    return TestClient(app)


@pytest.fixture
def report():
    class Embedder:
        def encode(self, texts):
            return np.eye(len(texts))

    root = Path(__file__).resolve().parents[1]
    request = AnalysisRequest(cv_text=(root / "examples/cv.txt").read_text(encoding="utf-8"),
                              job_text=(root / "examples/job.txt").read_text(encoding="utf-8"))
    return analyze(request, Embedder()).model_dump()


def test_save_reopen_persist_delete(store_client, report):
    assert store_client.get("/api/analyses").json() == {"items": [], "total": 0}
    created = store_client.post("/api/analyses", json={"title": "Mon bilan", "result": report, "is_demo": True})
    assert created.status_code == 201
    item = created.json()
    assert item["is_demo"] is True
    assert "result" not in item
    # A new connection and fresh schema initialization preserve saved reports.
    storage.initialize()
    reopened = store_client.get(f"/api/analyses/{item['id']}")
    assert reopened.status_code == 200
    assert reopened.json()["result"] == report
    assert store_client.get("/api/analyses").json()["total"] == 1
    assert store_client.delete(f"/api/analyses/{item['id']}").status_code == 204
    assert store_client.get(f"/api/analyses/{item['id']}").status_code == 404
    assert store_client.delete(f"/api/analyses/{item['id']}").status_code == 404


def test_pagination_and_parameterized_titles(store_client, report):
    title = "'); DROP TABLE analyses; --"
    for index in range(3):
        assert store_client.post("/api/analyses", json={"title": title + str(index), "result": report}).status_code == 201
    page = store_client.get("/api/analyses?limit=2&offset=0").json()
    second = store_client.get("/api/analyses?limit=2&offset=2").json()
    assert page["total"] == second["total"] == 3
    assert len(page["items"]) == 2
    assert len(second["items"]) == 1
    assert not ({i["id"] for i in page["items"]} & {i["id"] for i in second["items"]})
    assert store_client.get("/api/analyses?limit=0").status_code == 422
    assert store_client.get("/api/analyses?offset=-1").status_code == 422


def test_reject_invalid_saved_report_and_no_implicit_persistence(store_client, report):
    assert store_client.post("/api/analyses", json={"title": "   ", "result": report}).status_code == 422
    assert store_client.post("/api/analyses", json={"title": "x" * 101, "result": report}).status_code == 422
    report["score"] = 120
    assert store_client.post("/api/analyses", json={"title": "Invalid", "result": report}).status_code == 422
    assert store_client.get("/api/analyses").json()["total"] == 0
    with sqlite3.connect(storage.database_path()) as db:
        assert db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0] == 0

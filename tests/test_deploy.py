"""Deployment behaviour: demo account seeding, shared JWT secret, Vercel routing."""
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import main, storage
from backend.analysis import analyze
from backend.config import settings

ROOT = Path(__file__).resolve().parents[1]


class FakeEmbedder:
    def encode(self, texts):
        return np.eye(len(texts))


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "database_path", lambda: tmp_path / "demo.sqlite3")
    monkeypatch.setattr("backend.auth.database_path", lambda: tmp_path / "demo.sqlite3")
    monkeypatch.setattr(main, "analyze", lambda request: analyze(request, FakeEmbedder()))
    storage.initialize()


def test_demo_account_is_seeded_once_and_can_log_in(fresh_db):
    main.seed_demo()
    main.seed_demo()  # idempotent: a restart must not duplicate the account or its report
    client = TestClient(main.app)
    login = client.post("/api/auth/connexion", json={"email": main.DEMO_ACCOUNT["email"],
                                                     "mot_de_passe": main.DEMO_ACCOUNT["mot_de_passe"]})
    assert login.status_code == 200
    reports = client.get("/api/analyses", headers={"Authorization": f"Bearer {login.json()['access_token']}"}).json()
    assert reports["total"] == 1 and reports["items"][0]["is_demo"] is True


def test_shared_jwt_secret_is_used_when_configured(fresh_db, monkeypatch):
    from backend.auth import signing_key
    monkeypatch.setattr(settings(), "jwt_secret", "x" * 40)
    assert signing_key() == "x" * 40


def test_vercel_routes_api_to_the_function_and_the_rest_to_react():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    rewrites = {r["source"]: r["destination"] for r in config["rewrites"]}
    assert rewrites["/api/(.*)"] == rewrites["/health"] == "/api/index"
    assert config["rewrites"][-1] == {"source": "/(.*)", "destination": "/index.html"}
    assert config["outputDirectory"] == "frontend-react/dist"
    assert (ROOT / "api/index.py").is_file()

"""Authentication and report isolation on a temporary SQLite database."""
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from backend import storage
from backend.auth import signing_key
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "database_path", lambda: tmp_path / "auth.sqlite3")
    # auth uses the same configurable path, without touching the real local key.
    monkeypatch.setattr("backend.auth.database_path", lambda: tmp_path / "auth.sqlite3")
    storage.initialize()
    return TestClient(app)


def register(client, email="alice@example.test"):
    account = {"nom": "Alice", "email": email, "mot_de_passe": "Test-passphrase-42"}
    response = client.post("/api/auth/inscription", json=account)
    assert response.status_code == 201
    assert "mot_de_passe_hash" not in response.json()
    login = client.post("/api/auth/connexion", json=account)
    assert login.status_code == 200
    return response.json(), {"Authorization": "Bearer " + login.json()["access_token"]}


def test_register_login_and_duplicate(client):
    user, headers = register(client)
    assert client.get("/api/auth/moi", headers=headers).json()["id"] == user["id"]
    assert client.post("/api/auth/inscription", json={"nom": "Autre", "email": "ALICE@example.test", "mot_de_passe": "Password-123"}).status_code == 409
    for email in ["alice@example.test", "missing@example.test"]:
        response = client.post("/api/auth/connexion", json={"email": email, "mot_de_passe": "wrong"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Email ou mot de passe incorrect."
    with storage.connection() as db:
        hashed = db.execute("SELECT mot_de_passe_hash FROM utilisateurs").fetchone()[0]
        assert hashed.startswith("$2b$")
        assert "Test-passphrase" not in hashed


def test_session_validation_and_password_limits(client):
    user, _ = register(client)
    assert client.get("/api/analyses").status_code == 401
    expired = jwt.encode({"sub": str(user["id"]), "exp": datetime.now(UTC) - timedelta(seconds=1)}, signing_key(), algorithm="HS256")
    for token in ["bad-token", expired]:
        assert client.get("/api/auth/moi", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    for password in ["short", "é" * 40]:
        assert client.post("/api/auth/inscription", json={"nom": "Test", "email": "new@example.test", "mot_de_passe": password}).status_code == 422


def test_private_reports_and_legacy_preservation(client):
    alice, alice_headers = register(client)
    _, bob_headers = register(client, "bob@example.test")
    # Storage-level fixtures need only score; API serialization is tested in test_storage.
    own = storage.save("Alice", {"score": 70}, utilisateur_id=alice["id"])
    legacy = storage.save("Before accounts", {"score": 60})
    assert client.get("/api/analyses", headers=alice_headers).json()["total"] == 1
    assert client.get("/api/analyses", headers=bob_headers).json()["total"] == 0
    for item in [own, legacy]:
        assert client.get(f"/api/analyses/{item['id']}", headers=bob_headers).status_code == 404
        assert client.delete(f"/api/analyses/{item['id']}", headers=bob_headers).status_code == 404
    storage.initialize()
    with storage.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM analyses").fetchone()[0] == 2

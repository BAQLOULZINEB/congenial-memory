from fastapi.testclient import TestClient

from backend.main import app


def test_react_spa_and_immutable_assets(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><div id='root'>Talent Match</div>", encoding="utf-8")
    (dist / "assets").mkdir()
    (dist / "assets" / "index-Ab12Cd34.js").write_text("console.log('built');", encoding="utf-8")
    monkeypatch.setattr("backend.main.FRONTEND_DIST", dist)
    client = TestClient(app)
    for route in ("/", "/analysis", "/results", "/plan"):
        response = client.get(route)
        assert response.status_code == 200
        assert "Talent Match" in response.text
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["content-type"].startswith("text/html")
        assert response.headers["x-content-type-options"] == "nosniff"
    response = client.get("/assets/index-Ab12Cd34.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["cache-control"]
    assert "javascript" in response.headers["content-type"]
    for route in ("/api/missing", "/assets/missing.js", "/missing.css", "/%2e%2e/secret.txt", "/health/missing"):
        assert client.get(route).status_code == 404
    assert client.get("/health").json()["status"] == "starting"
    assert client.get("/openapi.json").status_code == 200
    assert "Swagger UI" in client.get("/docs").text


def test_missing_build_does_not_hide_api(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.main.FRONTEND_DIST", tmp_path / "missing")
    client = TestClient(app)
    assert client.get("/").status_code == 503
    assert client.get("/health").status_code == 200
    assert client.get("/api/unknown").status_code == 404

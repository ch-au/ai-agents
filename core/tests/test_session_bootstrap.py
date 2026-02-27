from fastapi.testclient import TestClient

from api import server


def test_get_cors_allow_origins_requires_env_in_cloud_mode(monkeypatch):
    monkeypatch.setenv("APP_RUNTIME_MODE", "cloud")
    monkeypatch.delenv("CORS_ALLOW_ORIGINS", raising=False)

    try:
        server._get_cors_allow_origins()
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "CORS_ALLOW_ORIGINS" in str(exc)


def test_session_ws_url_uses_forwarded_headers_when_trusted(monkeypatch):
    monkeypatch.setenv("APP_RUNTIME_MODE", "cloud")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")

    async def fake_create_session():
        return {"session_id": "sid-123"}

    monkeypatch.setattr(server, "create_session", fake_create_session)

    with TestClient(server.app) as client:
        response = client.post(
            "/session",
            headers={
                "x-forwarded-proto": "https",
                "x-forwarded-host": "api.example.com",
                "host": "internal:8000",
            },
            json={},
        )

    assert response.status_code == 200
    assert response.json()["ws_url"] == "wss://api.example.com"


def test_session_ws_url_ignores_forwarded_headers_when_untrusted(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "false")

    async def fake_create_session():
        return {"session_id": "sid-456"}

    monkeypatch.setattr(server, "create_session", fake_create_session)

    with TestClient(server.app) as client:
        response = client.post(
            "/session",
            headers={
                "x-forwarded-proto": "https",
                "x-forwarded-host": "api.example.com",
                "host": "localhost:9999",
            },
            json={},
        )

    assert response.status_code == 200
    assert response.json()["ws_url"] == "ws://localhost:9999"

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.config import settings
from app.security import rate_limit, require_auth


def test_public_health_endpoint_remains_available():
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    assert TestClient(app).get("/health").status_code == 200


def test_protected_request_rejects_missing_authentication():
    app = FastAPI()

    @app.post("/protected", dependencies=[Depends(require_auth)])
    async def protected():
        return {"ok": True}

    original = settings.API_AUTH_TOKEN
    settings.API_AUTH_TOKEN = "test-token"
    try:
        assert TestClient(app).post("/protected").status_code == 401
    finally:
        settings.API_AUTH_TOKEN = original


def test_authenticated_request_succeeds():
    app = FastAPI()

    @app.post("/protected", dependencies=[Depends(require_auth)])
    async def protected():
        return {"ok": True}

    original = settings.API_AUTH_TOKEN
    settings.API_AUTH_TOKEN = "test-token"
    try:
        response = TestClient(app).post(
            "/protected",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
    finally:
        settings.API_AUTH_TOKEN = original


@pytest.mark.asyncio
async def test_rate_limit_rejects_after_configured_limit(monkeypatch):
    class FakeCache:
        redis_client = None
        in_memory_cache = {}

    monkeypatch.setattr("app.security.get_cache_service", lambda: FakeCache())
    monkeypatch.setattr(settings, "RATE_LIMIT_LEAD_REQUESTS", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    dependency = rate_limit("RATE_LIMIT_LEAD_REQUESTS")

    request = Request({
        "type": "http",
        "method": "POST",
        "path": "/protected",
        "raw_path": b"/protected",
        "headers": [],
        "client": ("test-client", 1234),
        "scheme": "http",
        "server": ("testserver", 80),
    })
    await dependency(request)
    with pytest.raises(Exception) as error:
        await dependency(request)
    assert getattr(error.value, "status_code", None) == 429

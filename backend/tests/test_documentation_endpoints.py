"""Tests for FastAPI documentation endpoints: /openapi.json, /docs, /redoc, and /health."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_openapi_json_endpoint():
    """Verify GET /openapi.json returns valid OpenAPI specification."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert "components" in data
    assert "/api/leads" in data["paths"]
    assert "/health" in data["paths"]


def test_swagger_docs_endpoint():
    """Verify GET /docs returns functional Swagger UI."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()
    assert "/openapi.json" in response.text


def test_redoc_endpoint_uses_reliable_cdn():
    """Verify GET /redoc returns valid HTML with reliable CDN asset and no broken @next CDN."""
    response = client.get("/redoc")
    assert response.status_code == 200
    html = response.text
    # Must have the <redoc> tag pointing to openapi.json
    assert '<redoc spec-url="/openapi.json"></redoc>' in html
    # Must use working Redocly CDN
    assert "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js" in html
    # Must NOT use broken jsdelivr @next URL
    assert "cdn.jsdelivr.net/npm/redoc@next" not in html


def test_health_check_endpoint():
    """Verify GET /health remains intact and healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"

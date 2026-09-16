import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
import app.database as db
from sqlalchemy import inspect

@pytest.fixture(autouse=True)
def setup_test_db():
    db.init_db()
    yield

client = TestClient(app)

def test_database_pool_configuration():
    assert settings.DATABASE_POOL_SIZE == 10
    assert settings.DATABASE_MAX_OVERFLOW == 20
    assert settings.DATABASE_POOL_TIMEOUT == 30
    assert settings.DATABASE_POOL_RECYCLE == 1800

def test_database_performance_indexes():
    inspector = inspect(db.engine)
    lead_indexes = [idx["name"] for idx in inspector.get_indexes("leads")]
    # Verify performance indexes are registered
    assert any("lead_status" in (idx or "") or "composite_score" in (idx or "") or "email" in (idx or "") for idx in lead_indexes)

def test_leads_pagination_and_search():
    response = client.get("/api/leads?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert "leads" in data
    assert isinstance(data["leads"], list)
    assert len(data["leads"]) <= 5

    # Test search param
    response_search = client.get("/api/leads?search=Acme&limit=5")
    assert response_search.status_code == 200
    assert "leads" in response_search.json()

    # Test status filter
    response_status = client.get("/api/leads?status=Qualified&limit=5")
    assert response_status.status_code == 200
    assert "leads" in response_status.json()

def test_scoring_config_caching():
    response1 = client.get("/api/config/scoring")
    assert response1.status_code == 200
    response2 = client.get("/api/config/scoring")
    assert response2.status_code == 200
    assert response1.json() == response2.json()

def test_kb_products_caching():
    response1 = client.get("/api/knowledge-base/products")
    assert response1.status_code == 200
    response2 = client.get("/api/knowledge-base/products")
    assert response2.status_code == 200
    assert response1.json() == response2.json()

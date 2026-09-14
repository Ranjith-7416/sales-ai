from pathlib import Path
from sqlalchemy.engine import make_url

from app.config import settings


def test_local_database_url_uses_compose_development_identity():
    url = make_url(settings.DATABASE_URL)

    assert url.username == "salesai"
    assert url.database == "salesai_db"
    assert "user:password" not in settings.DATABASE_URL


def test_compose_builds_backend_url_with_same_database_identity():
    compose = Path(__file__).parents[2].joinpath("docker-compose.yml").read_text()

    assert "POSTGRES_USER:-salesai" in compose
    assert "POSTGRES_DB:-salesai_db" in compose
    assert "postgresql://${POSTGRES_USER:-salesai}:${POSTGRES_PASSWORD:-salesai_password}@postgres:5432/${POSTGRES_DB:-salesai_db}" in compose
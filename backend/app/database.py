from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings
from app.models import Base
import logging

logger = logging.getLogger(__name__)

# Create engine
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    engine = create_engine(
        db_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if ":memory:" in db_url else None,
    )
else:
    engine = create_engine(
        db_url,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        connect_args={"connect_timeout": settings.DATABASE_CONNECT_TIMEOUT_SECONDS},
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_performance_indexes(bind_engine):
    """Safely and non-destructively ensure performance indexes exist on tables."""
    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_leads_status_created_at ON leads (lead_status, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS ix_leads_composite_score ON leads (composite_score)",
        "CREATE INDEX IF NOT EXISTS ix_leads_email ON leads (email)",
        "CREATE INDEX IF NOT EXISTS ix_proposals_lead_created ON proposals (lead_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS ix_proposals_status ON proposals (status)",
    ]
    with bind_engine.connect() as conn:
        for stmt in index_statements:
            try:
                from sqlalchemy import text
                conn.execute(text(stmt))
                conn.commit()
            except Exception as e:
                logger.debug(f"Index creation note ({stmt}): {e}")


def init_db():
    """Initialize database - create all tables and performance indexes"""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        _ensure_performance_indexes(engine)
        logger.info("Database tables and performance indexes initialized")
    except Exception as exc:
        if settings.ENVIRONMENT.lower() != "production":
            logger.warning("PostgreSQL unavailable (%s); using SQLite for local development", exc)
            engine = create_engine(
                "sqlite:///./salesai_dev.db",
                echo=settings.DEBUG,
                connect_args={"check_same_thread": False},
            )
            SessionLocal.configure(bind=engine)
            Base.metadata.create_all(bind=engine)
            _ensure_performance_indexes(engine)
            logger.info("Development SQLite database tables and performance indexes initialized")
        else:
            raise


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")

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
        pool_recycle=3600,
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


def init_db():
    """Initialize database - create all tables"""
    global engine, SessionLocal
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized")
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
            logger.info("Development SQLite database tables initialized")
        else:
            raise


def drop_db():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")

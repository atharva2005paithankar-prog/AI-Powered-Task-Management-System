"""Database connection: engine, session factory and the Base class for models."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# SQLite (used only by the automated tests) needs this extra option.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# pool_pre_ping checks a connection is alive before using it.
engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Every database model inherits from this class."""


def get_db():
    """FastAPI dependency: one database session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

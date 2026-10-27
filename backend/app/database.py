"""SQLAlchemy engine/session wiring.

Uses the standard SQLAlchemy 2.0 declarative pattern so the only thing that
needs to change to run against Postgres (or any other SQLAlchemy-supported
database) instead of the default SQLite file is the ``DATABASE_URL``
environment variable -- nothing here is SQLite-specific except the
``check_same_thread`` connect arg, which SQLAlchemy only needs for SQLite
and which is skipped for every other dialect.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Fine for a demo-scale app; a real production
    deployment would use Alembic migrations instead."""
    from app import models  # noqa: F401  (ensures models are registered on Base)

    Base.metadata.create_all(bind=engine)

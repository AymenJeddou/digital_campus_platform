"""Database session factory for the AI retrieval layer.

Provides a lightweight SQLAlchemy session bound to ``DATABASE_URL`` (the same
PostgreSQL + pgvector instance the backend uses). Kept independent of the
backend package so the AI module can run standalone; semantic search uses raw
SQL, so no ORM models are required here.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load ai/.env (DATABASE_URL, keys) regardless of the working directory.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


@lru_cache(maxsize=1)
def _session_factory():
    load_dotenv(_ENV_PATH)
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Semantic search needs a PostgreSQL + "
            "pgvector connection (set it in ai/.env or the environment)."
        )
    engine = create_engine(url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    """Return a new SQLAlchemy session bound to ``DATABASE_URL``."""
    return _session_factory()()

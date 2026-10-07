"""Wipe the local database and rebuild it from the Alembic migrations.

DESTRUCTIVE: every table (users, chats, embedded knowledge base) is dropped.
Refuses to run unless DATABASE_URL points at localhost, and asks you to type
the database name to confirm.

    python scripts/reset_db.py
"""
import subprocess
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.database import engine  # noqa: E402


def reset_database():
    url = make_url(settings.DATABASE_URL)
    if url.host not in ("localhost", "127.0.0.1"):
        sys.exit(f"Refusing to reset a non-local database ({url.host}).")
    answer = input(f"This deletes ALL data in '{url.database}' on {url.host}:{url.port}. Type the database name to confirm: ")
    if answer.strip() != url.database:
        sys.exit("Cancelled.")

    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=backend_dir, check=True)
    print("Database reset. Run scripts/ingest_kb.py to reload the knowledge base.")


if __name__ == "__main__":
    reset_database()

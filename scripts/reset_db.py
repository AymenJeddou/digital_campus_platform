import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import Base, engine
# Import all models to ensure they are registered with Base
from app.models import models

def reset_database():
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables with updated schema...")
    Base.metadata.create_all(bind=engine)
    
    print("Database reset successfully! You can now run ingest_kb.py if needed.")

if __name__ == "__main__":
    reset_database()

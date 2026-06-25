from fastapi import FastAPI
from app.db.database import Base, engine
from app.models import models
from app.api.routes import auth, profile

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Digital Campus API")

app.include_router(auth.router)
app.include_router(profile.router)

@app.get("/")
def root():
    return {"message": "Digital Campus API is running"}
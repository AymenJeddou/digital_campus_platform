from fastapi import FastAPI
from app.db.database import Base, engine
from app.models import models
from app.api.routes import auth, profile, chat, documents

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Digital Campus API")

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(documents.router)

@app.get("/")
def root():
    return {"message": "Digital Campus API is running"}
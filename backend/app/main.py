import sys
from pathlib import Path

# Ensure the repo root is importable so the backend can load the AI package
# (ai.integration / ai.rag) regardless of how uvicorn is launched.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.database import Base, engine, ensure_schema
from app.models import models
from app.api.routes import auth, profile, chat, documents, courses
from app.core.dependencies import get_current_user

Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(title="Digital Campus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def protected_route_guard(request, call_next):
    # Never block CORS preflight — it carries no Authorization header. Letting
    # OPTIONS through allows the CORS middleware to answer the preflight.
    if request.method == "OPTIONS":
        return await call_next(request)
    # Google's OAuth redirect lands here as a plain browser navigation — no
    # Authorization header is possible. It authenticates via the signed
    # `state` query param instead (see routes/courses.py::classroom_callback).
    if request.url.path == "/courses/classroom/callback":
        return await call_next(request)
    protected_prefixes = ("/profile", "/chat", "/documents", "/onboarding/status", "/courses")
    if request.url.path.startswith(protected_prefixes) and not request.headers.get("authorization"):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return await call_next(request)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(courses.router)


@app.get("/onboarding/status")
def onboarding_status(current_user=Depends(get_current_user)):
    return {
        "onboarding_completed": current_user.onboarding_completed,
        "student_status": current_user.student_status,
        "academic_year": current_user.academic_year,
    }

@app.get("/")
def root():
    return {"message": "Digital Campus API is running"}
import sys
from pathlib import Path

# Ensure the repo root is importable so the backend can load the AI package
# (ai.integration / ai.rag) regardless of how uvicorn is launched.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.db.database import Base, engine, ensure_schema
from app.models import models
from app.api.routes import auth, profile, chat, documents, courses
from app.core.dependencies import get_current_user
from app.core.config import settings

Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(title="Digital Campus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Warm the heavy singletons so the FIRST real request doesn't pay the
    # ~30s embedding-model load (and the LLM clients are built once). Best-effort:
    # a warmup failure must not stop the API from starting.
    import logging
    log = logging.getLogger("startup")
    try:
        from ai.rag.embeddings import embed_query
        embed_query("warmup")
        from ai.llm.client import get_llm
        import os
        get_llm()
        get_llm(model=os.getenv("GROUNDEDNESS_GRADER_MODEL"))
        log.info("Warmup complete: embedding model + LLM clients ready.")
    except Exception:
        log.exception("Warmup failed (continuing to serve).")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
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
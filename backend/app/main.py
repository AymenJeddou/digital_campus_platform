import sys
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure the repo root is importable so the backend can load the AI package
# (ai.integration / ai.rag) regardless of how uvicorn is launched.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# uvicorn only configures its own loggers; without a root handler our app
# loggers (services/rag.py, warmup, groundedness warnings) are swallowed.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    force=True,
)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import admin, auth, chat, courses, documents, meta, profile
from app.core.config import settings

log = logging.getLogger("startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the heavy singletons so the FIRST real request doesn't pay the
    # ~30s embedding-model load. Best-effort: a warmup failure (e.g. no LLM
    # key yet) must not stop the API from serving.
    try:
        from ai.rag.embeddings import embed_query
        from ai.llm.client import get_llm

        embed_query("warmup")
        get_llm()
        get_llm(model=os.getenv("GROUNDEDNESS_GRADER_MODEL"))
        log.info("Warmup complete: embedding model + LLM clients ready.")
    except Exception as exc:
        log.warning("Warmup incomplete (continuing to serve): %s", exc)
    yield


app = FastAPI(title="Digital Campus API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": exc.errors()})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger("app").exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


for module in (auth, profile, chat, documents, courses, admin, meta):
    app.include_router(module.router)


@app.get("/")
def root():
    return {"message": "Digital Campus API is running"}

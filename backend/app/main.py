from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.database import Base, engine, ensure_schema
from app.models import models
from app.api.routes import auth, profile, chat, documents
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
    protected_prefixes = ("/profile", "/chat", "/documents", "/onboarding/status")
    if request.url.path.startswith(protected_prefixes) and not request.headers.get("authorization"):
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    return await call_next(request)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(documents.router)


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
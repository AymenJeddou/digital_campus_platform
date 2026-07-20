from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_TLS: bool = True
    RAG_PIPELINE_HANDLER: str | None = None
    # Local/dev only: auto-verify new accounts so login works without SMTP.
    # MUST stay False in production (the real email flow is the gate).
    AUTO_VERIFY_EMAIL: bool = False

    # Google Classroom / Drive OAuth
    GOOGLE_CLASSROOM_CLIENT_ID: str | None = None
    GOOGLE_CLASSROOM_CLIENT_SECRET: str | None = None
    GOOGLE_CLASSROOM_REDIRECT_URI: str = "http://localhost:8000/courses/classroom/callback"
    FRONTEND_URL: str = "http://localhost:3000"
    GOOGLE_TOKEN_ENCRYPTION_KEY: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
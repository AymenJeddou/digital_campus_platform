from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    # Session length. The token sits in an httpOnly cookie and can be revoked
    # on logout, so a working day is a reasonable lifetime.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
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

    FRONTEND_URL: str = "http://localhost:3000"

    # Redis (rate limiting / token bucket for /auth/login).
    REDIS_URL: str = "redis://localhost:6379"

    # Google Classroom / Drive OAuth (courses feature). Tokens are encrypted at
    # rest with GOOGLE_TOKEN_ENCRYPTION_KEY; the OAuth callback uses a signed state.
    GOOGLE_CLASSROOM_CLIENT_ID: str | None = None
    GOOGLE_CLASSROOM_CLIENT_SECRET: str | None = None
    GOOGLE_CLASSROOM_REDIRECT_URI: str = "http://localhost:8000/courses/classroom/callback"
    GOOGLE_TOKEN_ENCRYPTION_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
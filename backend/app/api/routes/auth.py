from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Student
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    VerifyEmailRequest,
    VerificationResponse,
)
from app.core.security import hash_password, verify_password, create_access_token, decode_token, validate_password
from app.core.config import settings
from app.services.email import send_verification_email
from fastapi_limiter.depends import RateLimiter
from app.models.models import RevokedToken
from app.core.dependencies import get_current_user
import uuid
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _create_verification_token(email: str) -> str:
    return create_access_token(data={"sub": email, "purpose": "email_verification"})


def _create_login_token(email: str, jti: str = None) -> str:
    return create_access_token(data={"sub": email, "purpose": "login"}, jti=jti)

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        validate_password(request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    existing = db.query(Student).filter(Student.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    student = Student(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        is_verified=settings.AUTO_VERIFY_EMAIL,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    if not settings.AUTO_VERIFY_EMAIL:
        send_verification_email(student.email, _create_verification_token(student.email))
    return {
        "message": "Account created successfully",
        "email": student.email,
    }


@router.post("/verify", response_model=VerificationResponse)
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.token)
    if not payload or payload.get("purpose") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid verification token")

    email = payload.get("sub")
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        raise HTTPException(status_code=404, detail="User not found")

    student.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}

from fastapi import Request
from redis.asyncio import Redis

redis_client = Redis(host="localhost", port=6379, encoding="utf-8", decode_responses=True)

async def login_rate_limiter(request: Request):
    # Temporarily bypassed for local development to prevent Redis timeouts
    return

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == form_data.username).first()
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not student.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    
    jti = str(uuid.uuid4())
    token = _create_login_token(student.email, jti=jti)
    return {"access_token": token, "token_type": "bearer"}

from app.core.dependencies import oauth2_scheme

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Student = Depends(get_current_user), 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    if payload:
        jti = payload.get("jti")
        if jti:
            revoked = RevokedToken(jti=jti)
            db.add(revoked)
            db.commit()
    return None
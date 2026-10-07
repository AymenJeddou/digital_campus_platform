import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.config import settings
from app.core.dependencies import get_current_user, oauth2_scheme
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    password_fingerprint,
    validate_password,
    verify_password,
)
from app.db.database import get_db
from app.models.models import RevokedToken, Student
from app.schemas.auth import (
    EmailRequest,
    MessageResponse,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Same answer whether or not the address exists, so these endpoints can't be
# used to discover who has an account.
_RESEND_MESSAGE = "If this address has an unverified account, a new link has been sent."
_FORGOT_MESSAGE = "If an account exists for this address, a reset link has been sent."


def _create_verification_token(email: str) -> str:
    return create_access_token(data={"sub": email, "purpose": "email_verification"})


def _create_reset_token(student: Student) -> str:
    return create_access_token(data={
        "sub": student.email,
        "purpose": "password_reset",
        "pwh": password_fingerprint(student.hashed_password),
    })


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        validate_password(request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if db.query(Student).filter(Student.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    student = Student(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name.strip(),
        is_verified=settings.AUTO_VERIFY_EMAIL,
    )
    db.add(student)
    db.commit()
    if not settings.AUTO_VERIFY_EMAIL:
        send_verification_email(student.email, _create_verification_token(student.email))
    return {"message": "Account created successfully", "email": student.email}


@router.post("/verify", response_model=MessageResponse)
def verify_email(request: VerifyEmailRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.token)
    if not payload or payload.get("purpose") != "email_verification":
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    student = db.query(Student).filter(Student.email == payload.get("sub")).first()
    if not student:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    student.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(body: EmailRequest, request: Request, db: Session = Depends(get_db)):
    await rate_limit.hit(f"resend:{body.email.lower()}", 3, 3600, "Too many requests. Try again later.")
    await rate_limit.hit(f"resend-ip:{_client_ip(request)}", 10, 3600, "Too many requests. Try again later.")
    student = db.query(Student).filter(Student.email == body.email).first()
    if student and not student.is_verified:
        send_verification_email(student.email, _create_verification_token(student.email))
    return {"message": _RESEND_MESSAGE}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: EmailRequest, request: Request, db: Session = Depends(get_db)):
    await rate_limit.hit(f"forgot:{body.email.lower()}", 3, 3600, "Too many requests. Try again later.")
    await rate_limit.hit(f"forgot-ip:{_client_ip(request)}", 10, 3600, "Too many requests. Try again later.")
    student = db.query(Student).filter(Student.email == body.email).first()
    if student:
        send_password_reset_email(student.email, _create_reset_token(student))
    return {"message": _FORGOT_MESSAGE}


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    payload = decode_token(body.token)
    invalid = HTTPException(status_code=400, detail="Invalid or expired reset link")
    if not payload or payload.get("purpose") != "password_reset":
        raise invalid
    student = db.query(Student).filter(Student.email == payload.get("sub")).first()
    # The fingerprint ties the token to the password it was issued for, so a
    # used (or superseded) link no longer works.
    if not student or payload.get("pwh") != password_fingerprint(student.hashed_password):
        raise invalid
    try:
        validate_password(body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    student.hashed_password = hash_password(body.password)
    student.is_verified = True  # the link was delivered to this inbox
    db.commit()
    return {"message": "Password updated"}


async def login_rate_limiter(request: Request):
    """Throttle per client IP and per targeted account, so neither one IP
    spraying many accounts nor many IPs hammering one account gets far."""
    form = await request.form()
    await rate_limit.hit(f"login:{_client_ip(request)}", 10, 60, "Too many login attempts. Try again later.")
    username = str(form.get("username", "")).lower()
    if username:
        await rate_limit.hit(f"login-account:{username}", 5, 60, "Too many login attempts. Try again later.")


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == form_data.username).first()
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not student.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    token = create_access_token(data={"sub": student.email, "purpose": "login"}, jti=str(uuid.uuid4()))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    current_user: Student = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    jti = (decode_token(token) or {}).get("jti")
    if jti:
        db.add(RevokedToken(jti=jti))
        db.commit()

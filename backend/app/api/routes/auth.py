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
from app.core.security import hash_password, verify_password, create_access_token, decode_token
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _create_verification_token(email: str) -> str:
    return create_access_token(data={"sub": email, "purpose": "email_verification"})

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    student = Student(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        is_verified=False,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    verification_token = _create_verification_token(student.email)
    send_verification_email(student.email, verification_token)
    return {
        "message": "Account created successfully",
        "email": student.email,
        "verification_token": verification_token,
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

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == form_data.username).first()
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not student.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    
    token = create_access_token(data={"sub": student.email})
    return {"access_token": token, "token_type": "bearer"}
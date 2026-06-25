from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import Student
from app.schemas.auth import RegisterRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    student = Student(
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return {"message": "Account created successfully", "email": student.email}

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == form_data.username).first()
    if not student or not verify_password(form_data.password, student.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(data={"sub": student.email})
    return {"access_token": token, "token_type": "bearer"}
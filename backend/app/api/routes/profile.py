from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student
from app.schemas.profile import ProfileResponse, ProfileUpdate, AcademicYearUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileResponse)
def get_profile(current_user: Student = Depends(get_current_user)):
    return current_user

@router.patch("", response_model=ProfileResponse)
def update_profile(
    updates: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user)
):
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.student_status is not None:
        current_user.student_status = updates.student_status
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/onboarding/status")
def onboarding_status(current_user: Student = Depends(get_current_user)):
    return {
        "onboarding_completed": current_user.onboarding_completed,
        "student_status": current_user.student_status,
        "academic_year": current_user.academic_year
    }

@router.patch("/academic-year", response_model=ProfileResponse)
def update_academic_year(
    body: AcademicYearUpdate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user)
):
    current_user.academic_year = body.academic_year
    db.commit()
    db.refresh(current_user)
    return current_user
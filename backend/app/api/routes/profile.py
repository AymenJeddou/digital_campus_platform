from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.models import Program, Student
from app.schemas.profile import AcademicYearUpdate, OnboardingRequest, ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


def _apply(db: Session, student: Student, fields: dict) -> None:
    """Copy validated fields onto the student (role is never settable here:
    the schemas don't expose it, and student_status is a closed Literal)."""
    program_id = fields.get("program_id")
    if program_id is not None and not db.get(Program, program_id):
        raise HTTPException(status_code=400, detail="Unknown program")
    for key, value in fields.items():
        setattr(student, key, value)


@router.get("", response_model=ProfileResponse)
def get_profile(current_user: Student = Depends(get_current_user)):
    return current_user


@router.patch("", response_model=ProfileResponse)
def update_profile(
    updates: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    _apply(db, current_user, updates.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/onboarding", response_model=ProfileResponse)
def complete_onboarding(
    body: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    _apply(db, current_user, body.model_dump(exclude_none=True))
    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/academic-year", response_model=ProfileResponse)
def update_academic_year(
    body: AcademicYearUpdate,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    current_user.academic_year = body.academic_year
    db.commit()
    db.refresh(current_user)
    return current_user

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student
from app.schemas.profile import ProfileResponse, ProfileUpdate, AcademicYearUpdate, OnboardingRequest

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
        if updates.student_status in {"admin", "enrolled"}:
            raise HTTPException(status_code=400, detail="student_status cannot be set through profile updates")
        current_user.student_status = updates.student_status
    if updates.bac_type is not None:
        current_user.bac_type = updates.bac_type
    if updates.bac_score is not None:
        current_user.bac_score = updates.bac_score
    if updates.interests is not None:
        current_user.interests = updates.interests
    if updates.goals is not None:
        current_user.goals = updates.goals
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/onboarding", response_model=ProfileResponse)
def complete_onboarding(
    body: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: Student = Depends(get_current_user),
):
    """Complete onboarding. This is the ONLY endpoint that can set
    student_status="enrolled" (which makes the Academic agent reachable).
    "admin" stays rejected here too."""
    if body.student_status not in {"prospective", "enrolled"}:
        raise HTTPException(status_code=400, detail="student_status must be 'prospective' or 'enrolled'")
    current_user.student_status = body.student_status
    if body.academic_year is not None:
        current_user.academic_year = body.academic_year
    if body.bac_type is not None:
        current_user.bac_type = body.bac_type
    if body.bac_score is not None:
        current_user.bac_score = body.bac_score
    if body.interests is not None:
        current_user.interests = body.interests
    if body.goals is not None:
        current_user.goals = body.goals
    current_user.onboarding_completed = True
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
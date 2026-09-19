from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfileResponse(BaseModel):
    email: str
    full_name: Optional[str]
    student_status: Optional[str]
    academic_year: Optional[str]
    bac_type: Optional[str] = None
    bac_score: Optional[float] = None
    interests: Optional[list[str]] = None
    goals: Optional[list[str]] = None
    enrollment_date: Optional[datetime]
    onboarding_completed: bool

    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    student_status: Optional[str] = None
    bac_type: Optional[str] = None
    bac_score: Optional[float] = None
    interests: Optional[list[str]] = None
    goals: Optional[list[str]] = None

class AcademicYearUpdate(BaseModel):
    academic_year: str

class OnboardingRequest(BaseModel):
    # The only place a student can become "enrolled". "admin" stays rejected.
    student_status: str  # "prospective" | "enrolled"
    academic_year: Optional[str] = None
    bac_type: Optional[str] = None
    bac_score: Optional[float] = None
    interests: Optional[list[str]] = None
    goals: Optional[list[str]] = None
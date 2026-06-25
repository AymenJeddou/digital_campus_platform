from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfileResponse(BaseModel):
    email: str
    full_name: Optional[str]
    student_status: Optional[str]
    academic_year: Optional[int]
    enrollment_date: Optional[datetime]
    onboarding_completed: bool

    class Config:
        from_attributes = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    student_status: Optional[str] = None

class AcademicYearUpdate(BaseModel):
    academic_year: int
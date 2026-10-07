import uuid
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Profile fields are injected into the assistant's system prompt, so they are
# restricted to short plain labels: letters, digits, spaces, apostrophes and
# hyphens. No newlines, braces or punctuation that could smuggle instructions.
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40, pattern=r"^[\w\s'’\-.]+$")]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80, pattern=r"^[\w\s'’\-.,/&+]+$")]
Status = Literal["prospective", "enrolled", "alumni"]


class ProgramRef(BaseModel):
    id: uuid.UUID
    name: str
    level: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    email: str
    full_name: Optional[str]
    role: Optional[str] = "student"
    student_status: Optional[str]
    academic_year: Optional[str]
    program: Optional[ProgramRef] = None
    bac_type: Optional[str] = None
    bac_score: Optional[float] = None
    interests: Optional[list[str]] = None
    goals: Optional[list[str]] = None
    enrollment_date: Optional[datetime]
    onboarding_completed: bool

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=120)
    student_status: Optional[Status] = None
    academic_year: Optional[Label] = None
    program_id: Optional[uuid.UUID] = None
    bac_type: Optional[Label] = None
    bac_score: Optional[float] = Field(None, ge=0, le=300)
    interests: Optional[list[Tag]] = Field(None, max_length=15)
    goals: Optional[list[Tag]] = Field(None, max_length=15)


class AcademicYearUpdate(BaseModel):
    academic_year: Label


class OnboardingRequest(BaseModel):
    student_status: Literal["prospective", "enrolled"]
    academic_year: Optional[Label] = None
    program_id: Optional[uuid.UUID] = None
    bac_type: Optional[Label] = None
    bac_score: Optional[float] = Field(None, ge=0, le=300)
    interests: Optional[list[Tag]] = Field(None, max_length=15)
    goals: Optional[list[Tag]] = Field(None, max_length=15)

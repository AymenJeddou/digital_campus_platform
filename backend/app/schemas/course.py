from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class CourseResponse(BaseModel):
    id: uuid.UUID
    name: str
    program_id: Optional[uuid.UUID] = None
    code: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class CourseEnrollRequest(BaseModel):
    course_id: uuid.UUID


class CourseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    code: Optional[str] = None
    description: Optional[str] = None


class EnrolledCourseResponse(CourseResponse):
    enrolled_at: datetime
    source: str
    material_count: int = 0


class CourseMaterialCreate(BaseModel):
    title: str
    content: str = Field(..., min_length=1, description="Raw text content of the material (manual path).")


class CourseMaterialResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    source: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    original_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    materials: list[CourseMaterialResponse] = Field(default_factory=list)


class ClassroomAuthorizeResponse(BaseModel):
    authorization_url: str


class ClassroomStatusResponse(BaseModel):
    connected: bool
    connected_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None


class ClassroomSyncedCourse(BaseModel):
    id: uuid.UUID
    name: str
    materials_synced: int


class ClassroomSyncResponse(BaseModel):
    courses_synced: int
    materials_synced: int
    courses: list[ClassroomSyncedCourse] = Field(default_factory=list)

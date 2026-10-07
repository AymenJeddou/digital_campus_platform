import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CourseResponse(BaseModel):
    id: uuid.UUID
    name: str
    program_id: Optional[uuid.UUID] = None
    code: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CourseEnrollRequest(BaseModel):
    course_id: uuid.UUID


class CourseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    code: Optional[str] = Field(None, max_length=40)
    description: Optional[str] = Field(None, max_length=2000)


class EnrolledCourseResponse(CourseResponse):
    enrolled_at: datetime
    source: str
    material_count: int = 0


class CourseMaterialCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=500_000, description="Raw text of the material.")


class CourseMaterialResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    source: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    original_filename: Optional[str] = None
    due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(CourseResponse):
    source: str = "manual"
    materials: list[CourseMaterialResponse] = Field(default_factory=list)


class ClassroomAuthorizeResponse(BaseModel):
    authorization_url: str


class ClassroomConnectRequest(BaseModel):
    code: str = Field(..., max_length=2048)
    state: str = Field(..., max_length=2048)


class ClassroomStatusResponse(BaseModel):
    connected: bool
    connected_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    sync_status: str = "idle"  # idle | running | success | error
    sync_courses_synced: int = 0
    sync_materials_synced: int = 0
    sync_materials_failed: int = 0
    sync_error: Optional[str] = None


class ClassroomSyncResponse(BaseModel):
    # "running" when a background sync was started; the frontend then polls
    # GET /courses/classroom/status for progress and completion.
    status: str = "running"
    courses_synced: int = 0
    materials_synced: int = 0
    materials_failed: int = 0

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

MAX_MESSAGE_CHARS = 4000


class ChatRequest(BaseModel):
    message: str = Field("", max_length=MAX_MESSAGE_CHARS)
    session_id: Optional[uuid.UUID] = None
    # When set, the assistant also searches this course's materials (scoped to
    # the current student). Omitted -> global knowledge base only.
    course_id: Optional[uuid.UUID] = None
    # Re-answer the session's last question instead of asking a new one
    # (``message`` is ignored; ``session_id`` is required).
    regenerate: bool = False


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    citations: list[Any] = Field(default_factory=list)


class SessionResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    citations: Optional[list[Any]] = None
    grounded: Optional[bool] = None
    created_at: datetime
    rating: Optional[int] = None  # this user's feedback on the message, if any

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel
from pydantic import Field
from typing import Optional
from typing import Any
import uuid

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[uuid.UUID] = None
    # When set, the assistant also searches this course's materials (scoped to
    # the current student). Omitted -> global knowledge base only.
    course_id: Optional[uuid.UUID] = None

class ChatResponse(BaseModel):
    session_id: uuid.UUID
    answer: str
    citations: list[Any] = Field(default_factory=list)
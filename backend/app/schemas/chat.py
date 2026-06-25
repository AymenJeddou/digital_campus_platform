from pydantic import BaseModel
from typing import Optional
import uuid

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[uuid.UUID] = None

class ChatResponse(BaseModel):
    session_id: uuid.UUID
    response: str
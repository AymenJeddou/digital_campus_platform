from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class FeedbackCreate(BaseModel):
    chat_message_id: uuid.UUID
    rating: int
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    chat_message_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

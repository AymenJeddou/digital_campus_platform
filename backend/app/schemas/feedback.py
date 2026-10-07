import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    chat_message_id: uuid.UUID
    rating: Literal[0, 1]  # 1 = helpful, 0 = not helpful
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    chat_message_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

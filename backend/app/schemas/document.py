from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    uploaded_at: datetime
    is_ingested: Optional[bool] = False
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)

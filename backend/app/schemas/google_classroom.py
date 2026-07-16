from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GoogleAuthURLResponse(BaseModel):
    url: str

class GoogleTokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    scope: str
    token_type: str

class GoogleClassroomTokenResponse(BaseModel):
    student_id: str
    expires_at: datetime
    scope: str

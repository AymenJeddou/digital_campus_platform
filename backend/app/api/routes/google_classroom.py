from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import Student, GoogleClassroomToken
from app.schemas.google_classroom import GoogleAuthURLResponse
from app.core.config import settings
import httpx
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/google-classroom", tags=["Google Classroom"])

@router.get("/auth-url", response_model=GoogleAuthURLResponse)
def get_auth_url(current_user: Student = Depends(get_current_user)):
    scopes = "https://www.googleapis.com/auth/classroom.courses.readonly"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"url": url}

@router.get("/auth-callback")
async def auth_callback(code: str = Query(...), db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve token")
        
        token_data = response.json()
    
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))
    
    google_token = db.query(GoogleClassroomToken).filter(GoogleClassroomToken.student_id == current_user.id).first()
    if google_token:
        google_token.access_token = token_data["access_token"]
        if "refresh_token" in token_data:
            google_token.refresh_token = token_data["refresh_token"]
        google_token.expires_at = expires_at
        google_token.scope = token_data.get("scope", "")
    else:
        google_token = GoogleClassroomToken(
            student_id=current_user.id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scope=token_data.get("scope", "")
        )
        db.add(google_token)
        
    db.commit()
    return {"message": "Google Classroom linked successfully"}

@router.get("/courses")
async def get_courses(db: Session = Depends(get_db), current_user: Student = Depends(get_current_user)):
    google_token = db.query(GoogleClassroomToken).filter(GoogleClassroomToken.student_id == current_user.id).first()
    if not google_token:
        raise HTTPException(status_code=400, detail="Google Classroom not linked")
        
    if google_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Token expired, please reconnect")
        
    url = "https://classroom.googleapis.com/v1/courses"
    headers = {"Authorization": f"Bearer {google_token.access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch courses")
            
        return response.json()

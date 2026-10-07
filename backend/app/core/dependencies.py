from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.models import RevokedToken, Student

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Student:
    payload = decode_token(token)
    # A login token must have a jti (every login issues one) so it can be revoked.
    if not payload or payload.get("purpose") != "login" or not payload.get("jti"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if db.query(RevokedToken).filter(RevokedToken.jti == payload["jti"]).first():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    student = db.query(Student).filter(Student.email == payload.get("sub")).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return student


def require_admin(current_user: Student = Depends(get_current_user)) -> Student:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

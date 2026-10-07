from datetime import datetime, timedelta, timezone
from typing import Optional
import re

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except ValueError:  # malformed stored hash
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, jti: Optional[str] = None) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    if jti:
        to_encode["jti"] = jti
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Mirrored client-side on the register / reset-password forms.
PASSWORD_RULES = (
    (r".{8,}", "Password must be at least 8 characters long"),
    (r"[A-Z]", "Password must contain at least one uppercase letter"),
    (r"[a-z]", "Password must contain at least one lowercase letter"),
    (r"[0-9]", "Password must contain at least one digit"),
    (r"[^A-Za-z0-9]", "Password must contain at least one special character"),
)


def validate_password(password: str):
    for pattern, message in PASSWORD_RULES:
        if not re.search(pattern, password):
            raise ValueError(message)
    if len(password.encode()) > 72:  # bcrypt ignores everything past 72 bytes
        raise ValueError("Password must be at most 72 bytes long")
    return True


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def password_fingerprint(hashed_password: str) -> str:
    """Tag of the current password hash, embedded in reset tokens so a token
    stops working as soon as the password changes (i.e. it is single-use)."""
    return hashed_password[-12:]

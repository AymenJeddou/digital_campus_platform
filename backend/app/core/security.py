from datetime import datetime, timedelta
from jose import JWTError, jwt
try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover - fallback for environments without passlib
    class CryptContext:  # minimal stub to provide clearer error when used
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "passlib is required for password hashing. Install with: pip install passlib[bcrypt]"
            )
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
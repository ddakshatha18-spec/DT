import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import jwt
from backend.app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password by matching SHA-256 hashes."""
    current_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return current_hash == hashed_password

def get_password_hash(password: str) -> str:
    """Generate SHA-256 hash."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encode JWT access token with expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

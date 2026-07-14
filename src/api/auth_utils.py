from datetime import datetime, timedelta, timezone
import jwt
import os


SECRET_KEY = os.getenv("RAG_SECRET_KEY", "2dfda5c476a91a869b1f6131a78b00a8ec4f93ca084b8bd5")
ALGORITHM = "HS256"


def create_access_token(user_id: int, expires_delta_days: int = 7) -> str:
    """Generates a secure JWT token containing the user_id that expires in 7 days."""
    expire = datetime.now(timezone.utc) + timedelta(days=expires_delta_days)
    
    payload = {
        "sub": str(user_id),  # 'sub' subject is standard practice for storing the user ID
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> int | None:
    """Decodes a JWT token and returns the embedded user_id if valid, or None if expired/corrupted."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except jwt.PyJWTError:
        return None  # Token is either expired, tampered with, or invalid

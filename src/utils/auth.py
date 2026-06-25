import jwt
import datetime
from typing import Optional, Dict, Any
from src.config import config

# A secret key for signing JWT tokens. In production, this should be in .env
JWT_SECRET = getattr(config, "JWT_SECRET", "auction_iq_secure_secret_998811")
JWT_ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    """Generates a JWT token for the user."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24) # Default 24h
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None

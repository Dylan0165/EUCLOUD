"""
FastAPI JWT Authentication with SSO Cookie Support
EU-CORE-BACKEND - Central authentication for all EUsuite apps
Supports both Authorization header (legacy) and HttpOnly cookies (SSO)
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
import os
import logging

from models import get_db, User

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# SSO Cookie Configuration
COOKIE_NAME = "eusuite_token"
COOKIE_MAX_AGE = 86400  # 24 hours in seconds

# Security scheme (optional for backwards compatibility)
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    user_id: Optional[int] = None


def create_access_token(user_id: int) -> str:
    """
    Create a JWT access token
    Note: user_id is stored as integer in payload (no 'subject must be a string' bug)
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "user_id": user_id,  # Store as int, not string
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db = Depends(get_db)
) -> User:
    """
    SSO Cookie Authentication Dependency
    
    Authentication priority:
    1. First try Authorization header (Bearer token) - for backwards compatibility
    2. Then try HttpOnly cookie (eusuite_token) - for SSO
    3. If both missing or invalid → 401
    
    This is the heart of the SSO system - all apps use /auth/me which depends on this.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = None
    
    # Priority 1: Try Authorization header
    if credentials:
        token = credentials.credentials
        logger.debug("Token found in Authorization header")
    
    # Priority 2: Try cookie
    if not token:
        token = request.cookies.get(COOKIE_NAME)
        if token:
            logger.debug("Token found in cookie")
    
    # No token found in either location
    if not token:
        logger.warning("No token found in Authorization header or cookie")
        raise credentials_exception
    
    # Validate JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            logger.warning("Token payload missing user_id")
            raise credentials_exception
            
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if user is None:
        logger.warning(f"User with id {user_id} not found in database")
        raise credentials_exception
    
    logger.debug(f"User {user.email} authenticated successfully")
    return user


def authenticate_user(db, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not user.check_password(password):
        return None
    
    return user

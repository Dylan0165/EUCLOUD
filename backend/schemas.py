"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=72,
        description="Password must be between 8 and 72 characters"
    )


class UserLogin(BaseModel):
    username: Optional[str] = None  # Accept username for compatibility
    email: Optional[EmailStr] = None  # Accept email 
    password: str = Field(..., max_length=72)
    
    @property
    def identifier(self):
        """Return either username or email as the login identifier"""
        return self.username or self.email


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: int
    email: str
    storage_quota: int
    storage_used: int
    storage_available: int
    created_at: str

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    access_token: str
    user: UserResponse

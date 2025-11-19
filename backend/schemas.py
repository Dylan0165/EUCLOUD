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
    email: Optional[str] = None  # Accept email (changed from EmailStr for flexibility)
    password: str = Field(..., max_length=72)
    
    def get_identifier(self) -> str:
        """Return either username or email as the login identifier"""
        identifier = self.username or self.email
        if not identifier:
            raise ValueError("Either username or email must be provided")
        return identifier.lower().strip()  # Normalize for case-insensitive lookup


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

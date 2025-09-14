"""
Authentication schemas for FastAPI.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, constr

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """User creation schema."""
    password: constr(min_length=8)
    email: EmailStr
    full_name: str

class UserUpdate(UserBase):
    """User update schema."""
    password: Optional[constr(min_length=8)] = None

class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str

class UserInDB(UserBase):
    """User in database schema."""
    id: int
    hashed_password: str

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    """User response schema."""
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Token schema."""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str

class RefreshToken(BaseModel):
    """Refresh token schema."""
    refresh_token: str
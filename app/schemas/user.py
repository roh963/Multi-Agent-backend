from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    """
    Signup endpoint pe user jo data bhejta hai uska schema.
    Pydantic automatically validate karta hai — galat data aaya toh 422 error.
    """
    email: EmailStr          # Pydantic khud check karta hai valid email format
    password: str
    name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Password validation — sirf length check nahi, basic rules enforce karo.
        Yeh validator automatically chalta hai jab Pydantic data parse kare.
        """
        if len(v) < 8:
            raise ValueError("Password kam se kam 8 characters ka hona chahiye")
        return v


class UserLogin(BaseModel):
    """Login request ka schema"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str          # ✅ str rakho
    email: str
    name: Optional[str]
    picture: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v) -> str:
        return str(v)   # ✅ UUID ya str — dono handle hoga


class AuthResponse(BaseModel):
    """
    Login/Signup dono ka unified response format.
    Frontend ko ek consistent shape milti hai.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

TokenResponse = AuthResponse
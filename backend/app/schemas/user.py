from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from backend.app.models.user import UserRole, WarningLevel

class UserBase(BaseModel):
    roll_number: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    offense_count: int
    warning_status: WarningLevel
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfile(UserResponse):
    pass

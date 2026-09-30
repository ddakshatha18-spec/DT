from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    roll_number: str = Field(..., description="Student roll number or Staff/Admin ID, e.g. '21CS001' or 'ADMIN01'", example="21CS001")
    password: str = Field(..., description="Password for authentication", example="emergency123")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class TokenPayload(BaseModel):
    sub: str  # roll_number
    user_id: int
    role: str
    exp: Optional[int] = None

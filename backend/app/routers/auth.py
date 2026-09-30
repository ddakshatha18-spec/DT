from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.auth import LoginRequest, TokenResponse
from backend.app.schemas.user import UserResponse, UserProfile
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User, UserRole
from backend.app.routers.deps import get_current_user, require_roles
from backend.app.core.rate_limiter import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """
    Roll-number based login for Students, Security Desk Admins, and Department HODs.
    Returns Bearer JWT token with user profile and active warning status.
    Protected by brute-force rate limiter.
    """
    login_rate_limiter.check(login_data.roll_number.strip().upper())
    
    user = AuthService.authenticate_user(db, roll_number=login_data.roll_number, password=login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid roll number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthService.create_user_token(user)

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    Renew active session token for continuous dashboard monitoring (Admin / Security desk).
    """
    return AuthService.create_user_token(current_user)

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Get the currently authenticated user's profile and offense warning tier."""
    return current_user

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)) -> Any:
    """Logout the authenticated user session."""
    return {"message": f"Successfully logged out {current_user.roll_number}"}

@router.get("/users/students", response_model=list[UserResponse])
def list_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOD))
) -> Any:
    """List all registered students (Admin & HOD access)."""
    return db.query(User).filter(User.role == UserRole.STUDENT).all()

@router.get("/users/{roll_number}", response_model=UserResponse)
def get_user_by_roll(
    roll_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve profile information for a specific roll number."""
    user = AuthService.get_user_by_roll_number(db, roll_number)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with roll number {roll_number} not found")
    return user

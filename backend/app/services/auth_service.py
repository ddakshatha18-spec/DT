from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User, UserRole
from backend.app.core.security import verify_password, create_access_token

class AuthService:
    @staticmethod
    def get_user_by_roll_number(db: Session, roll_number: str) -> Optional[User]:
        return db.query(User).filter(User.roll_number == roll_number.strip().upper()).first()

    @staticmethod
    def authenticate_user(db: Session, roll_number: str, password: str) -> Optional[User]:
        user = AuthService.get_user_by_roll_number(db, roll_number)
        if not user:
            return None
        if not user.hashed_password:
            # If no password set, allow login for development/quick test or verify default
            return user
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_user_token(user: User) -> dict:
        access_token = create_access_token(
            data={
                "sub": user.roll_number,
                "user_id": user.id,
                "role": user.role.value
            }
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "roll_number": user.roll_number,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "role": user.role.value,
                "department": user.department,
                "offense_count": user.offense_count,
                "warning_status": user.warning_status.value,
                "is_active": user.is_active
            }
        }

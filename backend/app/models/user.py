import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"
    HOD = "hod"

class WarningLevel(str, enum.Enum):
    NONE = "none"
    WARNING = "warning"
    STRONG_WARNING = "strong_warning"
    REFERRED_TO_HIGHER_AUTHORITY = "referred_to_higher_authority"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    department = Column(String(100), nullable=True)
    
    # False alert escalation counters (as per Escalation Policy)
    offense_count = Column(Integer, default=0, nullable=False)
    warning_status = Column(Enum(WarningLevel), default=WarningLevel.NONE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    alerts = relationship("Alert", back_populates="student", cascade="all, delete-orphan")
    escalation_logs = relationship("EscalationLog", back_populates="student", cascade="all, delete-orphan")
    admin_actions = relationship("AdminAction", back_populates="admin")

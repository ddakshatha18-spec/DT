from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class EscalationLog(Base):
    __tablename__ = "escalation_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    offense_number = Column(Integer, nullable=False)
    warning_level = Column(String(50), nullable=False) # "warning", "strong_warning", "referred_to_higher_authority"
    action_taken = Column(String(255), nullable=False)
    remarks = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student = relationship("User", back_populates="escalation_logs")
    alert = relationship("Alert", back_populates="escalation_logs")

class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(50), nullable=False) # e.g. "ACKNOWLEDGE", "MARK_GENUINE", "MARK_FALSE", "ESCALATE"
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    admin = relationship("User", back_populates="admin_actions")
    alert = relationship("Alert", back_populates="admin_actions")

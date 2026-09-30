import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class EmergencyType(str, enum.Enum):
    FALL_INJURY = "Fall / Injury"
    MEDICAL_EMERGENCY = "Medical Emergency"
    ACCIDENT = "Accident"
    FIRE_SMOKE = "Fire / Smoke"
    HARASSMENT_THREAT = "Harassment / Threat"
    FAINTING_UNCONSCIOUSNESS = "Fainting / Unconsciousness"
    OTHER = "Other Emergency"

class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED_GENUINE = "RESOLVED_GENUINE"
    RESOLVED_FALSE = "RESOLVED_FALSE"
    ESCALATED = "ESCALATED"

class AlertPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. ALT-20261001-001
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    emergency_type = Column(Enum(EmergencyType), nullable=False)
    priority = Column(Enum(AlertPriority), default=AlertPriority.HIGH, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.NEW, nullable=False)
    
    # Structured indoor location
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, default=0, nullable=False)
    
    # Optional device coordinates & details
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    student = relationship("User", back_populates="alerts")
    building = relationship("Building", back_populates="alerts")
    status_history = relationship("AlertStatusHistory", back_populates="alert", cascade="all, delete-orphan", order_by="AlertStatusHistory.timestamp.asc()")
    escalation_logs = relationship("EscalationLog", back_populates="alert")
    admin_actions = relationship("AdminAction", back_populates="alert")

class AlertStatusHistory(Base):
    __tablename__ = "alert_status_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    remarks = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    alert = relationship("Alert", back_populates="status_history")
    changed_by = relationship("User")

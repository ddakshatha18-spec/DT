from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "ENG-B", "SCI-A", "LIB"
    name = Column(String(100), nullable=False)                          # e.g., "Engineering Block B"
    description = Column(String(255), nullable=True)
    total_floors = Column(Integer, default=4, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="building")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    room_number = Column(String(20), index=True, nullable=False)        # e.g., "302", "LAB-1", "AUD-1"
    floor = Column(Integer, nullable=False)                             # 0 (Ground), 1, 2, 3, etc.
    wing = Column(String(20), default="Main", nullable=True)            # "East", "West", "Main"
    room_type = Column(String(50), default="Classroom", nullable=False) # "Classroom", "Lab", "Faculty Room", "Washroom", "Auditorium"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Unique constraint per building and room_number
    __table_args__ = (
        UniqueConstraint("building_id", "room_number", name="uq_building_room"),
    )

    # Relationships
    building = relationship("Building", back_populates="rooms")

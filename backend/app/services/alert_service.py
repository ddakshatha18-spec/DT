import random
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.alert import Alert, AlertStatus, AlertPriority, EmergencyType, AlertStatusHistory
from backend.app.models.location import Building, Room
from backend.app.models.user import User
from backend.app.schemas.alert import AlertCreate
from backend.app.services.notification_service import NotificationService

class AlertService:
    @staticmethod
    def calculate_priority(emergency_type: EmergencyType) -> AlertPriority:
        """Assign triage priority level based on emergency hazard classification."""
        critical_types = {
            EmergencyType.FIRE_SMOKE,
            EmergencyType.MEDICAL_EMERGENCY,
            EmergencyType.HARASSMENT_THREAT
        }
        high_types = {
            EmergencyType.ACCIDENT,
            EmergencyType.FAINTING_UNCONSCIOUSNESS
        }
        if emergency_type in critical_types:
            return AlertPriority.CRITICAL
        elif emergency_type in high_types:
            return AlertPriority.HIGH
        else:
            return AlertPriority.MEDIUM

    @staticmethod
    def generate_alert_code() -> str:
        """Generate unique, human-readable alert code, e.g. ALT-20261001-4921."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        rand_num = random.randint(1000, 9999)
        return f"ALT-{date_str}-{rand_num}"

    @classmethod
    async def create_alert(cls, db: Session, student: User, alert_in: AlertCreate) -> Alert:
        """Validate location, determine priority, persist alert and trigger notification broadcast."""
        building = db.query(Building).filter(Building.id == alert_in.building_id).first()
        if not building:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Building with ID {alert_in.building_id} does not exist"
            )

        # Room lookup for automatic floor assignment if floor not specified
        room = db.query(Room).filter(
            Room.building_id == building.id,
            Room.room_number.ilike(alert_in.room_number.strip())
        ).first()

        assigned_floor = alert_in.floor if alert_in.floor is not None else (room.floor if room else 0)
        priority = cls.calculate_priority(alert_in.emergency_type)
        alert_code = cls.generate_alert_code()

        alert = Alert(
            alert_code=alert_code,
            student_id=student.id,
            emergency_type=alert_in.emergency_type,
            priority=priority,
            status=AlertStatus.NEW,
            building_id=building.id,
            room_number=alert_in.room_number.strip(),
            floor=assigned_floor,
            latitude=alert_in.latitude,
            longitude=alert_in.longitude,
            description=alert_in.description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(alert)
        db.flush()

        # Record initial status in history
        history = AlertStatusHistory(
            alert_id=alert.id,
            previous_status="INITIAL",
            new_status=AlertStatus.NEW.value,
            changed_by_user_id=student.id,
            remarks="Emergency triggered by student",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)
        db.commit()
        db.refresh(alert)

        # Broadcast real-time event to Admin Dashboard
        alert_dict = cls.format_alert_response(alert)
        await NotificationService.broadcast_alert("NEW_ALERT", alert_dict)

        return alert

    @staticmethod
    def format_alert_response(alert: Alert) -> dict:
        """Helper to serialize alert with relations."""
        return {
            "id": alert.id,
            "alert_code": alert.alert_code,
            "student_id": alert.student_id,
            "student_roll_number": alert.student.roll_number if alert.student else None,
            "student_name": alert.student.full_name if alert.student else None,
            "student_phone": alert.student.phone if alert.student else None,
            "emergency_type": alert.emergency_type.value if hasattr(alert.emergency_type, "value") else str(alert.emergency_type),
            "priority": alert.priority.value if hasattr(alert.priority, "value") else str(alert.priority),
            "status": alert.status.value if hasattr(alert.status, "value") else str(alert.status),
            "building_id": alert.building_id,
            "building_name": alert.building.name if alert.building else None,
            "building_code": alert.building.code if alert.building else None,
            "room_number": alert.room_number,
            "floor": alert.floor,
            "description": alert.description,
            "latitude": alert.latitude,
            "longitude": alert.longitude,
            "created_at": alert.created_at.isoformat(),
            "updated_at": alert.updated_at.isoformat(),
            "status_history": [
                {
                    "id": h.id,
                    "previous_status": h.previous_status,
                    "new_status": h.new_status,
                    "changed_by_user_id": h.changed_by_user_id,
                    "remarks": h.remarks,
                    "timestamp": h.timestamp.isoformat()
                }
                for h in alert.status_history
            ]
        }

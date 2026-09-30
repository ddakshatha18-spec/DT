from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User, WarningLevel
from backend.app.models.alert import Alert, AlertStatus, AlertStatusHistory
from backend.app.models.escalation import EscalationLog, AdminAction
from backend.app.services.notification_service import NotificationService

class EscalationService:
    @classmethod
    async def process_status_update(
        cls,
        db: Session,
        alert: Alert,
        admin_user: User,
        new_status: AlertStatus,
        remarks: Optional[str] = None
    ) -> dict:
        """
        Transition alert status, audit the administrative action,
        and trigger progressive human-in-the-loop escalation if marked as false alarm.
        """
        previous_status = alert.status.value if hasattr(alert.status, "value") else str(alert.status)
        alert.status = new_status
        alert.updated_at = datetime.now(timezone.utc)

        # 1. Log in AlertStatusHistory
        history = AlertStatusHistory(
            alert_id=alert.id,
            previous_status=previous_status,
            new_status=new_status.value,
            changed_by_user_id=admin_user.id,
            remarks=remarks,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(history)

        # 2. Log in AdminAction
        admin_action = AdminAction(
            admin_id=admin_user.id,
            alert_id=alert.id,
            action_type=f"STATUS_CHANGE_TO_{new_status.value}",
            comments=remarks,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(admin_action)

        escalation_triggered = False
        escalation_info = None

        # 3. Handle Escalation on False Alarm
        if new_status == AlertStatus.RESOLVED_FALSE:
            student = db.query(User).filter(User.id == alert.student_id).first()
            if student:
                student.offense_count += 1
                offense = student.offense_count

                if offense == 1:
                    student.warning_status = WarningLevel.WARNING
                    action_text = "1st False Alert: Formal warning issued and incident logged."
                elif offense == 2:
                    student.warning_status = WarningLevel.STRONG_WARNING
                    action_text = "2nd False Alert: Strong official warning issued; student and mentor notified."
                else:
                    student.warning_status = WarningLevel.REFERRED_TO_HIGHER_AUTHORITY
                    action_text = f"{offense}rd/Repeated False Alert: Persistent misuse referred to Higher Administration (Dean & Disciplinary Committee) for formal inquiry."

                esc_log = EscalationLog(
                    student_id=student.id,
                    alert_id=alert.id,
                    offense_number=offense,
                    warning_level=student.warning_status.value,
                    action_taken=action_text,
                    remarks=remarks,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(esc_log)
                escalation_triggered = True
                escalation_info = {
                    "offense_number": offense,
                    "warning_level": student.warning_status.value,
                    "action_taken": action_text,
                    "student_roll_number": student.roll_number
                }

        db.commit()
        db.refresh(alert)

        # 4. Broadcast live update to Dashboards
        await NotificationService.broadcast_alert(
            "ALERT_STATUS_UPDATED",
            {
                "alert_id": alert.id,
                "alert_code": alert.alert_code,
                "new_status": new_status.value,
                "previous_status": previous_status,
                "escalation_triggered": escalation_triggered,
                "escalation_info": escalation_info,
                "admin_roll_number": admin_user.roll_number
            }
        )

        return {
            "alert_id": alert.id,
            "alert_code": alert.alert_code,
            "previous_status": previous_status,
            "new_status": new_status.value,
            "escalation_triggered": escalation_triggered,
            "escalation_details": escalation_info,
            "message": f"Alert status successfully updated to {new_status.value}"
        }

    @staticmethod
    def get_escalation_logs(db: Session, limit: int = 50) -> list[EscalationLog]:
        return db.query(EscalationLog).order_by(EscalationLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_student_escalation_history(db: Session, roll_number: str) -> Optional[dict]:
        student = db.query(User).filter(User.roll_number == roll_number.strip().upper()).first()
        if not student:
            return None
        logs = db.query(EscalationLog).filter(EscalationLog.student_id == student.id).order_by(EscalationLog.timestamp.desc()).all()
        return {
            "roll_number": student.roll_number,
            "full_name": student.full_name,
            "department": student.department,
            "offense_count": student.offense_count,
            "warning_status": student.warning_status,
            "escalation_history": [
                {
                    "id": l.id,
                    "student_id": l.student_id,
                    "student_roll_number": student.roll_number,
                    "student_name": student.full_name,
                    "alert_id": l.alert_id,
                    "alert_code": l.alert.alert_code if l.alert else None,
                    "offense_number": l.offense_number,
                    "warning_level": l.warning_level,
                    "action_taken": l.action_taken,
                    "remarks": l.remarks,
                    "timestamp": l.timestamp
                }
                for l in logs
            ]
        }

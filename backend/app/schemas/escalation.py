from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.models.user import WarningLevel

class EscalationLogResponse(BaseModel):
    id: int
    student_id: int
    student_roll_number: Optional[str] = None
    student_name: Optional[str] = None
    alert_id: int
    alert_code: Optional[str] = None
    offense_number: int
    warning_level: WarningLevel
    action_taken: str
    remarks: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class StudentEscalationSummary(BaseModel):
    roll_number: str
    full_name: str
    department: Optional[str] = None
    offense_count: int
    warning_status: WarningLevel
    escalation_history: list[EscalationLogResponse] = []

    class Config:
        from_attributes = True

class StatusUpdateResult(BaseModel):
    alert_id: int
    alert_code: str
    previous_status: str
    new_status: str
    escalation_triggered: bool
    escalation_details: Optional[dict] = None
    message: str

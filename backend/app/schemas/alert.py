from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from backend.app.models.alert import EmergencyType, AlertStatus, AlertPriority

class AlertCreate(BaseModel):
    emergency_type: EmergencyType = Field(..., description="Predefined emergency type", example="Medical Emergency")
    building_id: int = Field(..., description="ID of campus building", example=1)
    room_number: str = Field(..., description="Room identifier", example="LAB-1")
    floor: Optional[int] = Field(None, description="Building floor (ground=0, 1, 2...)", example=1)
    description: Optional[str] = Field(None, description="Optional brief context", example="Student collapsed near workbench")
    latitude: Optional[float] = Field(None, description="Optional GPS latitude", example=12.9716)
    longitude: Optional[float] = Field(None, description="Optional GPS longitude", example=77.5946)

class AlertStatusHistoryResponse(BaseModel):
    id: int
    previous_status: str
    new_status: str
    changed_by_user_id: Optional[int]
    remarks: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True

class AlertResponse(BaseModel):
    id: int
    alert_code: str
    student_id: int
    student_roll_number: Optional[str] = None
    student_name: Optional[str] = None
    student_phone: Optional[str] = None
    emergency_type: EmergencyType
    priority: AlertPriority
    status: AlertStatus
    building_id: int
    building_name: Optional[str] = None
    building_code: Optional[str] = None
    room_number: str
    floor: int
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    status_history: list[AlertStatusHistoryResponse] = []

    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: AlertStatus = Field(..., description="Target status: ACKNOWLEDGED, RESOLVED_GENUINE, RESOLVED_FALSE, ESCALATED")
    remarks: Optional[str] = Field(None, description="Review remarks or notes", example="Medical team dispatched to room")

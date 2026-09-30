from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.alert import Alert, AlertStatus, AlertPriority
from backend.app.models.user import User, UserRole
from backend.app.schemas.alert import AlertCreate, AlertResponse
from backend.app.services.alert_service import AlertService
from backend.app.services.notification_service import NotificationService
from backend.app.routers.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["Emergency Alerts"])

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def submit_alert(
    alert_in: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Primary Emergency Submission API (Student App / Panic Button).
    Instantaneous room-level alerting with automatic hazard prioritization and dispatch.
    """
    alert = await AlertService.create_alert(db=db, student=current_user, alert_in=alert_in)
    return AlertService.format_alert_response(alert)

@router.get("/", response_model=list[AlertResponse])
def list_alerts(
    status_filter: Optional[AlertStatus] = Query(None, alias="status"),
    priority_filter: Optional[AlertPriority] = Query(None, alias="priority"),
    building_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    List alerts.
    - Security / Admin / HOD: views complete campus queue.
    - Students: views own alert history.
    """
    query = db.query(Alert)
    
    if current_user.role == UserRole.STUDENT:
        query = query.filter(Alert.student_id == current_user.id)
        
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    if priority_filter:
        query = query.filter(Alert.priority == priority_filter)
    if building_id:
        query = query.filter(Alert.building_id == building_id)
        
    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return [AlertService.format_alert_response(a) for a in alerts]

@router.get("/stream")
async def stream_live_alerts():
    """
    Server-Sent Events (SSE) live stream for Admin Dashboard / Security Monitor.
    Pushes real-time alerts instantaneously as students tap the emergency button.
    """
    queue = NotificationService.subscribe()
    return StreamingResponse(
        NotificationService.event_generator(queue),
        media_type="text/event-stream"
    )

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Retrieve complete metadata and status transition history of a specific alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert with ID {alert_id} not found")
        
    # Check permission
    if current_user.role == UserRole.STUDENT and alert.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to alert details")
        
    return AlertService.format_alert_response(alert)

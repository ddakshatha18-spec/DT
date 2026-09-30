from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.schemas.escalation import EscalationLogResponse, StudentEscalationSummary
from backend.app.services.escalation_service import EscalationService
from backend.app.routers.deps import require_roles

router = APIRouter(prefix="/escalation", tags=["Escalation & Accountability"])

@router.get("/logs", response_model=list[EscalationLogResponse])
def get_escalation_logs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOD))
) -> Any:
    """Retrieve full audit log of all progressive escalation events across campus."""
    logs = EscalationService.get_escalation_logs(db, limit)
    results = []
    for l in logs:
        results.append(
            EscalationLogResponse(
                id=l.id,
                student_id=l.student_id,
                student_roll_number=l.student.roll_number if l.student else None,
                student_name=l.student.full_name if l.student else None,
                alert_id=l.alert_id,
                alert_code=l.alert.alert_code if l.alert else None,
                offense_number=l.offense_number,
                warning_level=l.warning_level,
                action_taken=l.action_taken,
                remarks=l.remarks,
                timestamp=l.timestamp
            )
        )
    return results

@router.get("/student/{roll_number}", response_model=StudentEscalationSummary)
def get_student_escalation(
    roll_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.HOD))
) -> Any:
    """Retrieve active warning tier and disciplinary incident history for a specific student."""
    summary = EscalationService.get_student_escalation_history(db, roll_number)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {roll_number} not found"
        )
    return summary

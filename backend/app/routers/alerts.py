import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.alert import (
    AlertCreate,
    AlertDetailResponse,
    AlertResponse,
    AlertSummaryResponse,
    AlertUpdate,
    InvestigatorActionCreate,
)
from app.services import alert_service

router = APIRouter(
    tags=["Alerts"]
)

@router.post("/alerts/generate", response_model=dict)
def generate_alerts(db: Session = Depends(get_db)):
    """
    Generate new alerts for HIGH and MEDIUM priority predictions that don't have one.
    """
    count = alert_service.generate_alerts_from_predictions(db)
    return {"message": f"Generated {count} new alerts."}


@router.get("/alerts", response_model=List[dict])
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority (HIGH, MEDIUM, LOW)"),
    district: Optional[str] = Query(None, description="Filter by district"),
    complaint_id: Optional[str] = Query(None, description="Filter by complaint ID"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of alerts.
    """
    alerts = alert_service.get_alerts(
        db=db,
        status=status,
        priority=priority,
        district=district,
        complaint_id=complaint_id
    )
    return alerts


@router.get("/investigator/alerts/summary", response_model=AlertSummaryResponse)
def get_alert_summary(db: Session = Depends(get_db)):
    """
    Get dashboard summary statistics for alerts.
    """
    summary = alert_service.get_alert_summary(db)
    return AlertSummaryResponse(**summary)


@router.get("/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert_detail(alert_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve full details for an alert, including SHAP explanation.
    """
    detail = alert_service.get_alert_detail(db, alert_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Alert not found")
    return detail


@router.patch("/alerts/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(alert_id: uuid.UUID, update_data: AlertUpdate, db: Session = Depends(get_db)):
    """
    Update the status of an alert.
    """
    valid_statuses = ["NEW", "ACKNOWLEDGED", "IN_REVIEW", "ACTION_TAKEN", "CLOSED"]
    if update_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
        
    alert = alert_service.update_alert_status(db, alert_id, update_data.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/actions", response_model=dict)
def add_investigator_action(alert_id: uuid.UUID, action_data: InvestigatorActionCreate, db: Session = Depends(get_db)):
    """
    Record an investigator action against an alert.
    """
    action = alert_service.add_investigator_action(
        db=db, 
        alert_id=alert_id, 
        action_type=action_data.action_type, 
        notes=action_data.notes
    )
    if not action:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return {
        "message": "Action recorded successfully",
        "action_id": str(action.action_id)
    }

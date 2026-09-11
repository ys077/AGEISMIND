import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AlertBase(BaseModel):
    status: str = Field(..., description="Current status of the alert")


class AlertCreate(BaseModel):
    prediction_id: uuid.UUID = Field(..., description="ID of the associated prediction")
    status: str = Field("NEW", description="Initial status of the alert")


class AlertUpdate(BaseModel):
    status: str = Field(..., description="New status of the alert")


class AlertResponse(AlertBase):
    alert_id: uuid.UUID
    prediction_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvestigatorActionCreate(BaseModel):
    action_type: str = Field(..., description="Type of action taken (e.g., REVIEWED, ESCALATED, CLOSED)")
    notes: Optional[str] = Field(None, description="Investigator notes")


class AlertDetailResponse(BaseModel):
    alert_id: uuid.UUID
    prediction_id: uuid.UUID
    complaint_id: str
    withdrawal_location_id: str
    district: str
    probability: float
    rank: int
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    # SHAP details
    top_positive_factors: List[dict]
    top_negative_factors: List[dict]
    explanation_text: str


class AlertSummaryResponse(BaseModel):
    total_alerts: int
    new_alerts: int
    acknowledged_alerts: int
    in_review_alerts: int
    action_taken_alerts: int
    closed_alerts: int
    high_priority: int
    medium_priority: int
    low_priority: int

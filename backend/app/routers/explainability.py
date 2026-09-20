from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.explainability import (
    ExplainabilityResponse,
    SingleCandidateExplanationResponse,
    ModelExplainabilityResponse
)
from app.services import explainability_service

router = APIRouter(prefix="", tags=["Explainable AI"])

@router.get("/explanations/{complaint_id}", response_model=ExplainabilityResponse)
def get_case_explanation(complaint_id: str, db: Session = Depends(get_db)):
    """
    Returns the latest prediction explanation for the given complaint.
    Feature contributions describe how the model arrived at its score.
    They do not establish causation or criminal responsibility.
    Model training and evaluation use synthetic prototype data.
    """
    return explainability_service.get_case_explanation(complaint_id, db)

@router.get("/explanations/{complaint_id}/candidates/{location_id}", response_model=Optional[SingleCandidateExplanationResponse])
def get_candidate_explanation(complaint_id: str, location_id: str, db: Session = Depends(get_db)):
    """
    Returns explanation for a specific ranked candidate.
    Feature contributions describe how the model arrived at its score.
    They do not establish causation or criminal responsibility.
    Model training and evaluation use synthetic prototype data.
    """
    return explainability_service.get_candidate_explanation(complaint_id, location_id, db)

@router.get("/ml/explainability", response_model=ModelExplainabilityResponse)
def get_global_explainability():
    """
    Returns global model explainability and feature importance.
    Feature contributions describe how the model arrived at its score.
    They do not establish causation or criminal responsibility.
    Model training and evaluation use synthetic prototype data.
    """
    return explainability_service.get_global_explainability_info()

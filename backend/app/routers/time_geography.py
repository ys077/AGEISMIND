from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db
from app.schemas.time_geography import (
    TimeGeographyResponse, TemporalAnalysis, GeographicAnalysis, CandidateFeatureResponse
)
from app.services import time_geography_service

router = APIRouter(prefix="/analysis", tags=["Time & Geography"])

@router.get("/{complaint_id}/time-geography", response_model=TimeGeographyResponse)
def get_time_geography_analysis(complaint_id: str, db: Session = Depends(get_db)):
    result = time_geography_service.generate_time_geography_analysis(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint data not found")
    return result

@router.get("/{complaint_id}/time", response_model=TemporalAnalysis)
def get_time_analysis(complaint_id: str, db: Session = Depends(get_db)):
    result = time_geography_service.analyze_temporal(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint data not found")
    return result

@router.get("/{complaint_id}/geography", response_model=GeographicAnalysis)
def get_geography_analysis(complaint_id: str, db: Session = Depends(get_db)):
    result = time_geography_service.analyze_geography(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint data not found")
    return result

@router.get("/{complaint_id}/withdrawal-candidates/features", response_model=CandidateFeatureResponse)
def get_withdrawal_candidates_features(complaint_id: str, db: Session = Depends(get_db)):
    candidates = time_geography_service.analyze_withdrawal_candidates(complaint_id, db)
    if not candidates:
        # If empty but valid complaint, return empty list. If complaint doesn't exist, return 404
        from app.models import Complaint
        if not db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first():
            raise HTTPException(status_code=404, detail="Complaint not found")
            
    return CandidateFeatureResponse(
        complaint_id=complaint_id,
        candidates=candidates
    )

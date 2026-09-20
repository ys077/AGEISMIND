from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.prediction import PredictionResponse, ModelInfoResponse
from app.services.prediction_service import (
    generate_and_save_prediction,
    get_stored_prediction,
    get_model_info,
    start_prediction_job,
    PREDICTION_JOBS
)

router = APIRouter(tags=["Predictions"])

@router.post("/predictions/{complaint_id}/run", response_model=dict)
def run_prediction(complaint_id: str, db: Session = Depends(get_db)):
    try:
        job_id = start_prediction_job(complaint_id)
        return {"job_id": job_id, "complaint_id": complaint_id, "status": "PROCESSING"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed to start: {str(e)}")

@router.get("/predictions/jobs/{job_id}/status", response_model=dict)
def get_prediction_job_status(job_id: str):
    if job_id not in PREDICTION_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return PREDICTION_JOBS[job_id]

@router.get("/predictions/{complaint_id}", response_model=Optional[PredictionResponse])
def read_stored_prediction(
    complaint_id: str,
    top_k: Optional[int] = Query(10, ge=1, le=50, description="Limit top K candidates"),
    db: Session = Depends(get_db)
):
    result = get_stored_prediction(complaint_id, db, top_k=top_k)
    return result

@router.get("/ml/model-info", response_model=ModelInfoResponse, tags=["Machine Learning"])
def read_model_info():
    try:
        return get_model_info()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model info: {str(e)}")

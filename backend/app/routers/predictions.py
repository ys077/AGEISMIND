from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.prediction import PredictionResponse, ModelInfoResponse
from app.services.prediction_service import (
    generate_and_save_prediction,
    get_stored_prediction,
    get_model_info
)

router = APIRouter(tags=["Predictions"])

@router.post("/predictions/{complaint_id}", response_model=PredictionResponse)
def create_prediction(complaint_id: str, db: Session = Depends(get_db)):
    try:
        return generate_and_save_prediction(complaint_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/predictions/{complaint_id}", response_model=PredictionResponse)
def read_stored_prediction(
    complaint_id: str,
    top_k: Optional[int] = Query(None, ge=1, le=50, description="Limit top K candidates"),
    db: Session = Depends(get_db)
):
    result = get_stored_prediction(complaint_id, db, top_k=top_k)
    if not result:
        raise HTTPException(status_code=404, detail=f"No stored predictions found for complaint {complaint_id}")
    return result

@router.get("/ml/model-info", response_model=ModelInfoResponse, tags=["Machine Learning"])
def read_model_info():
    try:
        return get_model_info()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model info: {str(e)}")

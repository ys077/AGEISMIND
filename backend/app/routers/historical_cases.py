from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models import HistoricalCase
from app.schemas import HistoricalCaseResponse

router = APIRouter(prefix="/historical-cases", tags=["Historical Cases"])

@router.get("", response_model=List[HistoricalCaseResponse])
def get_historical_cases(
    district: Optional[str] = None,
    fraud_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(HistoricalCase)
    
    if district:
        query = query.filter(HistoricalCase.district_id == district)
    if fraud_type:
        query = query.filter(HistoricalCase.fraud_type == fraud_type)
        
    offset = (page - 1) * page_size
    cases = query.offset(offset).limit(page_size).all()
    return cases

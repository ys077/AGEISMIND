from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models import WithdrawalLocation
from app.schemas import WithdrawalLocationResponse

router = APIRouter(prefix="/withdrawal-locations", tags=["Withdrawal Locations"])

@router.get("", response_model=List[WithdrawalLocationResponse])
def get_withdrawal_locations(
    district: Optional[str] = None,
    location_type: Optional[str] = None,
    risk_level_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(WithdrawalLocation)
    
    if district:
        query = query.filter(WithdrawalLocation.district_id == district)
    if location_type:
        query = query.filter(WithdrawalLocation.location_type == location_type)
    if risk_level_min is not None:
        query = query.filter(WithdrawalLocation.area_risk_baseline >= risk_level_min)
        
    offset = (page - 1) * page_size
    locations = query.offset(offset).limit(page_size).all()
    return locations

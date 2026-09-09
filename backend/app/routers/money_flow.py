from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.money_flow import MoneyFlowResponse, AccountFlowResponse
from app.services import money_flow_service

router = APIRouter(prefix="/analysis", tags=["Money Flow"])

@router.get("/{complaint_id}/money-flow", response_model=MoneyFlowResponse)
def get_money_flow(complaint_id: str, db: Session = Depends(get_db)):
    result = money_flow_service.reconstruct_money_flow(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint or transactions not found")
    return result

@router.get("/{complaint_id}/money-flow/accounts/{account_id}", response_model=AccountFlowResponse)
def get_account_flow(complaint_id: str, account_id: str, db: Session = Depends(get_db)):
    result = money_flow_service.get_account_flow(complaint_id, account_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Account flow not found for this complaint")
    return result

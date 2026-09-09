from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.network_analysis import NetworkAnalysisResponse, NetworkGraphResponse, AccountNetworkResponse
from app.services import network_analysis_service

router = APIRouter(prefix="/analysis", tags=["Network Analysis"])

@router.get("/{complaint_id}/network-analysis", response_model=NetworkAnalysisResponse)
def get_network_analysis(complaint_id: str, db: Session = Depends(get_db)):
    result = network_analysis_service.analyze_network(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint network not found")
    return result

@router.get("/{complaint_id}/network-analysis/graph", response_model=NetworkGraphResponse)
def get_network_graph(complaint_id: str, db: Session = Depends(get_db)):
    result = network_analysis_service.get_network_graph(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint network not found")
    return result

@router.get("/{complaint_id}/network-analysis/accounts/{account_id}", response_model=AccountNetworkResponse)
def get_account_network(complaint_id: str, account_id: str, db: Session = Depends(get_db)):
    result = network_analysis_service.get_account_network(complaint_id, account_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Account network not found in this complaint")
    return result

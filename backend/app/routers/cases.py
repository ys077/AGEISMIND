from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.api.deps import get_db
from app.models import Complaint, Transaction, Account, AccountRelationship, WithdrawalLocation, HistoricalCase
from app.schemas import CompleteCaseResponse, NetworkResponse, NetworkNode, NetworkEdge
from app.routers.complaints import get_complaint_transactions, get_complaint_accounts, get_complaint_network

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("/{complaint_id}/complete", response_model=CompleteCaseResponse)
def get_complete_case(complaint_id: str, db: Session = Depends(get_db)):
    # 1. Complaint
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    # 2. Transactions
    transactions = get_complaint_transactions(complaint_id, db)
    
    # 3. Accounts
    accounts = get_complaint_accounts(complaint_id, db)
    account_ids = {a.account_id for a in accounts}
    
    # 4. Relationships
    relationships = []
    if account_ids:
        relationships = db.query(AccountRelationship).filter(
            (AccountRelationship.source_account.in_(account_ids)) &
            (AccountRelationship.target_account.in_(account_ids))
        ).all()
        
    # 5. Network (Reused from complaints router)
    network = get_complaint_network(complaint_id, db)
    
    # 6. Candidate Withdrawal Locations
    # Let's say candidate withdrawal locations are those in the complaint's district
    locations = db.query(WithdrawalLocation).filter(WithdrawalLocation.district_id == complaint.district_id).all()
    
    # 7. Historical Cases
    # Relevant historical cases in the same district or with the same fraud type
    historical_cases = db.query(HistoricalCase).filter(
        HistoricalCase.district_id == complaint.district_id,
        HistoricalCase.fraud_type == complaint.fraud_type
    ).all()
    
    return CompleteCaseResponse(
        complaint=complaint,
        transactions=transactions,
        accounts=accounts,
        relationships=relationships,
        network=network,
        candidate_withdrawal_locations=locations,
        historical_cases=historical_cases
    )

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Complaint, Transaction, Account
from app.schemas.analysis import (
    ComplaintAnalysisResponse,
    TransactionAnalysisResponse,
    CaseAnalysisResponse
)
from app.services import analysis_service

router = APIRouter(prefix="/analysis", tags=["Analysis"])

def _get_complaint_and_context(complaint_id: str, db: Session):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    
    senders = {t.sender_account for t in transactions}
    receivers = {t.receiver_account for t in transactions}
    account_ids = senders | receivers
    
    accounts = []
    if account_ids:
        accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
        
    return complaint, transactions, accounts

@router.get("/{complaint_id}", response_model=CaseAnalysisResponse)
def get_case_analysis(complaint_id: str, db: Session = Depends(get_db)):
    result = analysis_service.get_case_analysis(complaint_id, db)
    if not result:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return result

@router.get("/{complaint_id}/complaint", response_model=ComplaintAnalysisResponse)
def get_complaint_analysis(complaint_id: str, db: Session = Depends(get_db)):
    complaint, transactions, accounts = _get_complaint_and_context(complaint_id, db)
    return analysis_service.analyze_complaint(complaint, transactions, accounts)

@router.get("/{complaint_id}/transactions", response_model=TransactionAnalysisResponse)
def get_transaction_analysis(complaint_id: str, db: Session = Depends(get_db)):
    complaint, transactions, accounts = _get_complaint_and_context(complaint_id, db)
    return analysis_service.analyze_transactions(complaint, transactions, accounts)

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.api.deps import get_db
from app.models import Complaint, Transaction, Account, AccountRelationship
from app.schemas import (
    ComplaintResponse,
    TransactionResponse,
    AccountResponse,
    RelationshipResponse,
    NetworkResponse,
    NetworkNode,
    NetworkEdge
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])

from app.schemas.complaint import PaginatedComplaintResponse

@router.get("", response_model=PaginatedComplaintResponse)
def get_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    total = db.query(Complaint).count()
    complaints = db.query(Complaint).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedComplaintResponse(
        items=complaints,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint

@router.get("/{complaint_id}/transactions", response_model=List[TransactionResponse])
def get_complaint_transactions(complaint_id: str, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    return transactions

@router.get("/{complaint_id}/accounts", response_model=List[AccountResponse])
def get_complaint_accounts(complaint_id: str, db: Session = Depends(get_db)):
    # Accounts are inferred from the transactions related to the complaint
    senders = db.query(distinct(Transaction.sender_account)).filter(Transaction.complaint_id == complaint_id)
    receivers = db.query(distinct(Transaction.receiver_account)).filter(Transaction.complaint_id == complaint_id)
    account_ids = {r[0] for r in senders.all()} | {r[0] for r in receivers.all()}
    
    accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
    return accounts

@router.get("/{complaint_id}/relationships", response_model=List[RelationshipResponse])
def get_complaint_relationships(complaint_id: str, db: Session = Depends(get_db)):
    senders = db.query(distinct(Transaction.sender_account)).filter(Transaction.complaint_id == complaint_id)
    receivers = db.query(distinct(Transaction.receiver_account)).filter(Transaction.complaint_id == complaint_id)
    account_ids = {r[0] for r in senders.all()} | {r[0] for r in receivers.all()}
    
    if not account_ids:
        return []
        
    relationships = db.query(AccountRelationship).filter(
        (AccountRelationship.source_account.in_(account_ids)) |
        (AccountRelationship.target_account.in_(account_ids))
    ).all()
    return relationships

@router.get("/{complaint_id}/network", response_model=NetworkResponse)
def get_complaint_network(complaint_id: str, db: Session = Depends(get_db)):
    accounts = get_complaint_accounts(complaint_id, db)
    account_ids = {a.account_id for a in accounts}
    
    relationships = []
    if account_ids:
        relationships = db.query(AccountRelationship).filter(
            (AccountRelationship.source_account.in_(account_ids)) &
            (AccountRelationship.target_account.in_(account_ids))
        ).all()
        
    nodes = [
        NetworkNode(
            id=a.account_id,
            type=a.account_type,
            district_id=a.district_id,
            latitude=float(a.latitude),
            longitude=float(a.longitude)
        ) for a in accounts
    ]
    
    edges = [
        NetworkEdge(
            source=r.source_account,
            target=r.target_account,
            relationship_type=r.relationship_type,
            total_amount=float(r.total_amount)
        ) for r in relationships
    ]
    
    return NetworkResponse(
        complaint_id=complaint_id,
        nodes=nodes,
        edges=edges
    )

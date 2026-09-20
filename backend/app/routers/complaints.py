from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, noload, load_only
from sqlalchemy import distinct, func, desc, or_
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
    q: Optional[str] = Query(None, description="Search complaint ID, category, type, city, or status"),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    filters = []
    term = (q or "").strip()
    if term:
        like = f"%{term}%"
        filters.append(or_(
            Complaint.complaint_id.ilike(like),
            Complaint.crime_category.ilike(like),
            Complaint.fraud_type.ilike(like),
            Complaint.victim_city.ilike(like),
            Complaint.status.ilike(like),
        ))
    if status:
        filters.append(Complaint.status == status)
    if category:
        filters.append(Complaint.crime_category == category)
    if filters:
        query = query.filter(*filters)

    offset = (page - 1) * page_size
    total = query.with_entities(func.count(Complaint.complaint_id)).scalar() or 0
    complaints = (
        query.options(
            load_only(
                Complaint.complaint_id,
                Complaint.complaint_date,
                Complaint.complaint_time,
                Complaint.fraud_type,
                Complaint.fraud_amount,
                Complaint.victim_city,
                Complaint.victim_latitude,
                Complaint.victim_longitude,
                Complaint.crime_category,
                Complaint.source_channel,
                Complaint.status,
                Complaint.district_id,
            ),
            noload(Complaint.transactions),
            noload(Complaint.predictions),
            noload(Complaint.investigation_actions),
            noload(Complaint.district),
        )
        .order_by(desc(Complaint.complaint_date), Complaint.complaint_id)
        .offset(offset)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if page_size else 1
    
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

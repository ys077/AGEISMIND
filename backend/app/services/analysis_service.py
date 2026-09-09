from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.models import Complaint, Transaction, Account
from app.schemas import ComplaintResponse
from app.schemas.analysis import (
    ComplaintSeverityAnalysis,
    ComplaintAnalysisResponse,
    TransactionSummary,
    TransactionTimelineItem,
    GeographicSummary,
    TemporalSummary,
    TransactionIndicator,
    TransactionIndicatorEvidence,
    TransactionAnalysisResponse,
    CaseAnalysisResponse
)

def analyze_complaint(complaint: Complaint, transactions: List[Transaction], accounts: List[Account]) -> ComplaintAnalysisResponse:
    # Basic logic for severity
    amount = float(complaint.fraud_amount)
    tx_count = len(transactions)
    district_count = len({a.district_id for a in accounts})
    
    severity = "LOW"
    key_indicators = []
    
    if amount > 5000000 or (tx_count > 20 and district_count > 3):
        severity = "CRITICAL"
        if amount > 5000000:
            key_indicators.append("Extremely high reported loss (>50L)")
        if tx_count > 20 and district_count > 3:
            key_indicators.append("Highly distributed network movement")
    elif amount > 1000000 or (tx_count > 10 and district_count > 2):
        severity = "HIGH"
        if amount > 1000000:
            key_indicators.append("High reported loss (>10L)")
        if tx_count > 10 and district_count > 2:
            key_indicators.append("Complex network movement")
    elif amount > 100000 or tx_count > 5:
        severity = "MEDIUM"
        if amount > 100000:
            key_indicators.append("Significant reported loss (>1L)")
        if tx_count > 5:
            key_indicators.append("Multiple transactions involved")
    else:
        key_indicators.append("Standard case parameters")

    severity_analysis = ComplaintSeverityAnalysis(
        severity=severity,
        key_indicators=key_indicators
    )
    
    return ComplaintAnalysisResponse(
        complaint=ComplaintResponse.model_validate(complaint),
        analysis=severity_analysis
    )

def _get_transaction_summary(transactions: List[Transaction]) -> TransactionSummary:
    total_tx = len(transactions)
    if total_tx == 0:
        return TransactionSummary(
            total_transactions=0,
            successful_transactions=0,
            failed_transactions=0,
            pending_transactions=0,
            total_amount=0.0,
            average_amount=0.0,
            minimum_amount=0.0,
            maximum_amount=0.0
        )
        
    successful = [t for t in transactions if t.transaction_status.lower() in ("completed", "successful", "success")]
    failed = [t for t in transactions if t.transaction_status.lower() in ("failed", "rejected", "declined")]
    pending = [t for t in transactions if t.transaction_status.lower() in ("pending", "processing")]
    
    amounts = [float(t.amount) for t in transactions]
    
    return TransactionSummary(
        total_transactions=total_tx,
        successful_transactions=len(successful),
        failed_transactions=len(failed),
        pending_transactions=len(pending),
        total_amount=sum(amounts),
        average_amount=sum(amounts) / total_tx,
        minimum_amount=min(amounts),
        maximum_amount=max(amounts)
    )

def _get_timeline_and_temporal(transactions: List[Transaction]) -> Tuple[List[TransactionTimelineItem], TemporalSummary]:
    if not transactions:
        return [], TemporalSummary(
            first_transaction_timestamp=None,
            last_transaction_timestamp=None,
            total_duration_hours=0.0,
            average_transaction_gap_seconds=0.0,
            shortest_transaction_gap_seconds=0.0
        )
        
    # Sort transactions by time
    sorted_tx = sorted(transactions, key=lambda t: t.transaction_time)
    
    timeline = []
    for t in sorted_tx:
        # Note: We aren't querying the Account's district for each item here to save DB hits, 
        # but the schema allows Optional[str] for district.
        timeline.append(TransactionTimelineItem(
            transaction_id=t.transaction_id,
            timestamp=t.transaction_time.isoformat(),
            sender_account=t.sender_account,
            receiver_account=t.receiver_account,
            amount=float(t.amount),
            status=t.transaction_status
        ))
        
    first_time = sorted_tx[0].transaction_time
    last_time = sorted_tx[-1].transaction_time
    total_duration_hours = (last_time - first_time).total_seconds() / 3600.0
    
    gaps = []
    for i in range(1, len(sorted_tx)):
        gap = (sorted_tx[i].transaction_time - sorted_tx[i-1].transaction_time).total_seconds()
        gaps.append(gap)
        
    avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
    min_gap = min(gaps) if gaps else 0.0
    
    temporal = TemporalSummary(
        first_transaction_timestamp=first_time.isoformat(),
        last_transaction_timestamp=last_time.isoformat(),
        total_duration_hours=total_duration_hours,
        average_transaction_gap_seconds=avg_gap,
        shortest_transaction_gap_seconds=min_gap
    )
    
    return timeline, temporal

def _get_geographic_summary(complaint: Complaint, transactions: List[Transaction], accounts: List[Account]) -> GeographicSummary:
    victim_district = complaint.district_id
    
    # Using the accounts list to find unique districts
    account_districts = list({a.district_id for a in accounts})
    
    # We can assume transaction districts are just the districts of the involved accounts
    tx_districts = account_districts.copy()
    
    return GeographicSummary(
        victim_district=victim_district,
        transaction_districts=tx_districts,
        account_districts=account_districts,
        unique_district_count=len(set(account_districts + [victim_district]))
    )

def _get_indicators(transactions: List[Transaction], accounts: List[Account]) -> List[TransactionIndicator]:
    indicators = []
    
    if not transactions:
        return indicators
        
    sorted_tx = sorted(transactions, key=lambda t: t.transaction_time)
    
    # 1. Rapid transfer (gap < 5 mins)
    rapid_tx_ids = []
    for i in range(1, len(sorted_tx)):
        gap = (sorted_tx[i].transaction_time - sorted_tx[i-1].transaction_time).total_seconds()
        if gap < 300: # 5 minutes
            rapid_tx_ids.extend([sorted_tx[i-1].transaction_id, sorted_tx[i].transaction_id])
            
    if rapid_tx_ids:
        indicators.append(TransactionIndicator(
            type="RAPID_TRANSFER",
            severity="HIGH",
            description="Transactions occurred within a very short time interval (< 5 mins), indicating potential automated or rapid funds movement.",
            evidence=TransactionIndicatorEvidence(transaction_ids=list(set(rapid_tx_ids)))
        ))
        
    # 2. High value transfer
    high_value_ids = [t.transaction_id for t in transactions if float(t.amount) > 500000]
    if high_value_ids:
        indicators.append(TransactionIndicator(
            type="HIGH_VALUE_TRANSFER",
            severity="HIGH",
            description="One or more transactions involve amounts significantly larger than typical (>5L).",
            evidence=TransactionIndicatorEvidence(transaction_ids=high_value_ids)
        ))
        
    # 3. Geographic Movement
    account_map = {a.account_id: a.district_id for a in accounts}
    geo_tx_ids = []
    for t in transactions:
        sender_dist = account_map.get(t.sender_account)
        receiver_dist = account_map.get(t.receiver_account)
        if sender_dist and receiver_dist and sender_dist != receiver_dist:
            geo_tx_ids.append(t.transaction_id)
            
    if geo_tx_ids:
        indicators.append(TransactionIndicator(
            type="GEOGRAPHIC_MOVEMENT",
            severity="MEDIUM",
            description="Funds are moving across different district boundaries.",
            evidence=TransactionIndicatorEvidence(transaction_ids=geo_tx_ids)
        ))
        
    # 4. Failed Attempts
    failed_ids = [t.transaction_id for t in transactions if t.transaction_status.lower() in ("failed", "rejected", "declined")]
    if failed_ids:
        indicators.append(TransactionIndicator(
            type="FAILED_ATTEMPT",
            severity="LOW",
            description="Multiple failed or rejected transaction attempts detected.",
            evidence=TransactionIndicatorEvidence(transaction_ids=failed_ids)
        ))
        
    return indicators

def analyze_transactions(complaint: Complaint, transactions: List[Transaction], accounts: List[Account]) -> TransactionAnalysisResponse:
    summary = _get_transaction_summary(transactions)
    timeline, temporal = _get_timeline_and_temporal(transactions)
    geographic = _get_geographic_summary(complaint, transactions, accounts)
    indicators = _get_indicators(transactions, accounts)
    
    return TransactionAnalysisResponse(
        transaction_summary=summary,
        timeline=timeline,
        geographic_summary=geographic,
        temporal_summary=temporal,
        indicators=indicators
    )

def get_case_analysis(complaint_id: str, db: Session) -> CaseAnalysisResponse:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        return None
        
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    
    senders = {t.sender_account for t in transactions}
    receivers = {t.receiver_account for t in transactions}
    account_ids = senders | receivers
    
    accounts = []
    if account_ids:
        accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
        
    complaint_analysis = analyze_complaint(complaint, transactions, accounts)
    transaction_analysis = analyze_transactions(complaint, transactions, accounts)
    
    return CaseAnalysisResponse(
        complaint_analysis=complaint_analysis,
        transaction_analysis=transaction_analysis
    )

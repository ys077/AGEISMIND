from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from .complaint import ComplaintResponse

# Complaint Analysis
class ComplaintSeverityAnalysis(BaseModel):
    severity: str
    key_indicators: List[str]

class ComplaintAnalysisResponse(BaseModel):
    complaint: ComplaintResponse
    analysis: ComplaintSeverityAnalysis

# Transaction Analysis
class TransactionSummary(BaseModel):
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    total_amount: float
    average_amount: float
    minimum_amount: float
    maximum_amount: float

class TransactionTimelineItem(BaseModel):
    transaction_id: str
    timestamp: str
    sender_account: str
    receiver_account: str
    amount: float
    status: str
    district: Optional[str] = None

class TransactionIndicatorEvidence(BaseModel):
    transaction_ids: List[str]

class TransactionIndicator(BaseModel):
    type: str
    severity: str
    description: str
    evidence: TransactionIndicatorEvidence

class GeographicSummary(BaseModel):
    victim_district: str
    transaction_districts: List[str]
    account_districts: List[str]
    unique_district_count: int

class TemporalSummary(BaseModel):
    first_transaction_timestamp: Optional[str]
    last_transaction_timestamp: Optional[str]
    total_duration_hours: float
    average_transaction_gap_seconds: float
    shortest_transaction_gap_seconds: float

class TransactionAnalysisResponse(BaseModel):
    transaction_summary: TransactionSummary
    timeline: List[TransactionTimelineItem]
    geographic_summary: GeographicSummary
    temporal_summary: TemporalSummary
    indicators: List[TransactionIndicator]

# Case Analysis
class CaseAnalysisResponse(BaseModel):
    complaint_analysis: ComplaintAnalysisResponse
    transaction_analysis: TransactionAnalysisResponse

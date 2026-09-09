from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class FlowTransaction(BaseModel):
    transaction_id: str
    timestamp: str
    amount: float
    status: str

class FlowAccountBase(BaseModel):
    account_id: str
    account_type: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FlowAccount(FlowAccountBase):
    role: str # "SOURCE", "INTERMEDIARY", "TERMINAL", "UNKNOWN"
    total_incoming: float
    total_outgoing: float
    observed_remaining: float
    incoming_transactions: List[str]
    outgoing_transactions: List[str]

class MoneyFlowPath(BaseModel):
    path_id: str
    accounts: List[str]
    transactions: List[str]
    total_amount: float
    start_time: str
    end_time: str

class FlowPattern(BaseModel):
    type: str
    description: str
    accounts: List[str]
    transactions: List[str]

class MoneyFlowSummary(BaseModel):
    total_accounts: int
    source_accounts: int
    intermediary_accounts: int
    terminal_accounts: int
    total_successful_amount: float
    total_paths: int
    max_hops: int
    districts_involved: int

class WithdrawalAssociation(BaseModel):
    exists: bool
    locations: List[str] # List of location IDs

class MoneyFlowResponse(BaseModel):
    complaint_id: str
    source_accounts: List[FlowAccount]
    intermediary_accounts: List[FlowAccount]
    terminal_accounts: List[FlowAccount]
    paths: List[MoneyFlowPath]
    account_flows: List[FlowAccount]
    flow_patterns: List[FlowPattern]
    flow_summary: MoneyFlowSummary
    withdrawal_associations: List[WithdrawalAssociation]

class FlowTimingGap(BaseModel):
    from_transaction: str
    to_transaction: str
    time_gap_seconds: float
    amount_before: float
    amount_after: float

class AccountFlowResponse(BaseModel):
    account_id: str
    role: str
    district: Optional[str] = None
    incoming_transactions: List[FlowTransaction]
    outgoing_transactions: List[FlowTransaction]
    total_incoming: float
    total_outgoing: float
    observed_remaining: float
    time_gaps: List[FlowTimingGap]

from typing import List
from pydantic import BaseModel
from .complaint import ComplaintResponse
from .transaction import TransactionResponse
from .account import AccountResponse
from .relationship import RelationshipResponse, NetworkResponse
from .withdrawal_location import WithdrawalLocationResponse
from .historical_case import HistoricalCaseResponse

class CompleteCaseResponse(BaseModel):
    complaint: ComplaintResponse
    transactions: List[TransactionResponse]
    accounts: List[AccountResponse]
    relationships: List[RelationshipResponse]
    network: NetworkResponse
    candidate_withdrawal_locations: List[WithdrawalLocationResponse]
    historical_cases: List[HistoricalCaseResponse]

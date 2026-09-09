from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TransactionBase(BaseModel):
    transaction_id: str
    complaint_id: str
    sender_account: str
    receiver_account: str
    amount: float
    transaction_time: datetime
    transaction_type: str
    transaction_status: str


class TransactionResponse(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

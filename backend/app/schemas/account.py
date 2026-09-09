from pydantic import BaseModel, ConfigDict


class AccountBase(BaseModel):
    account_id: str
    district_id: str
    account_type: str
    city: str
    latitude: float
    longitude: float
    account_risk_score: float
    previous_case_count: int
    account_status: str


class AccountResponse(AccountBase):
    model_config = ConfigDict(from_attributes=True)

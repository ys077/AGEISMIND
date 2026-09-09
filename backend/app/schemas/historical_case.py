from pydantic import BaseModel, ConfigDict


class HistoricalCaseBase(BaseModel):
    historical_case_id: str
    district_id: str
    withdrawal_zone: str
    fraud_type: str
    fraud_amount: float
    transaction_hour: int
    city: str
    latitude: float
    longitude: float
    account_risk: float
    transaction_velocity: int
    distance_to_location: float
    atm_density: int
    historical_similarity: float
    outcome: str


class HistoricalCaseResponse(HistoricalCaseBase):
    model_config = ConfigDict(from_attributes=True)

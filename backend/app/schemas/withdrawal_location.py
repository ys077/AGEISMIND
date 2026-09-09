from typing import Optional
from pydantic import BaseModel, ConfigDict


class WithdrawalLocationBase(BaseModel):
    location_id: str
    district_id: str
    location_reference_id: Optional[str] = None
    location_name: str
    city: str
    latitude: float
    longitude: float
    location_type: str
    atm_count: int
    area_risk_baseline: float


class WithdrawalLocationResponse(WithdrawalLocationBase):
    model_config = ConfigDict(from_attributes=True)

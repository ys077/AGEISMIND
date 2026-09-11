from datetime import date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ComplaintBase(BaseModel):
    complaint_id: str
    complaint_date: date
    complaint_time: time
    fraud_type: str
    fraud_amount: float
    victim_city: str
    victim_latitude: float
    victim_longitude: float
    crime_category: str
    source_channel: str
    status: str
    district_id: str


class ComplaintResponse(ComplaintBase):
    model_config = ConfigDict(from_attributes=True)

class PaginatedComplaintResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

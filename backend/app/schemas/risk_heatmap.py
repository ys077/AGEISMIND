from typing import List, Optional
from pydantic import BaseModel, ConfigDict
import uuid

class HeatmapCandidate(BaseModel):
    prediction_id: str
    withdrawal_location_id: str
    latitude: float
    longitude: float
    district: str
    probability: float
    rank: int
    priority: str
    model_version: str
    source: Optional[str] = None
    source_id: Optional[str] = None
    operator: Optional[str] = None
    brand: Optional[str] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class HeatmapResponse(BaseModel):
    complaint_id: str
    map_type: str = "withdrawal_candidate_risk"
    candidates: List[HeatmapCandidate]

    model_config = ConfigDict(from_attributes=True)

class DistrictAggregation(BaseModel):
    district_name: str
    candidate_count: int
    highest_probability: float
    average_probability: float
    highest_rank: int

    model_config = ConfigDict(from_attributes=True)

class DistrictHeatmapResponse(BaseModel):
    complaint_id: str
    map_type: str = "withdrawal_candidate_risk_by_district"
    districts: List[DistrictAggregation]

    model_config = ConfigDict(from_attributes=True)

class GlobalHeatmapCandidate(BaseModel):
    location_id: str
    latitude: float
    longitude: float
    district: str
    complaint_count: int
    prediction_count: int
    average_probability: float
    maximum_probability: float
    risk_level: str

    model_config = ConfigDict(from_attributes=True)

class GlobalHeatmapResponse(BaseModel):
    map_type: str = "global_aggregated_risk"
    candidates: List[GlobalHeatmapCandidate]

    model_config = ConfigDict(from_attributes=True)

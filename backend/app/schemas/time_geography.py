from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==============================================================================
# TEMPORAL ANALYSIS
# ==============================================================================

class TimeGap(BaseModel):
    minimum_gap_minutes: float
    maximum_gap_minutes: float
    average_gap_minutes: float
    median_gap_minutes: float

class HourlyActivity(BaseModel):
    hour: int
    transaction_count: int
    total_amount: float

class DailyActivity(BaseModel):
    day_name: str
    transaction_count: int
    total_amount: float

class TimePeriodActivity(BaseModel):
    period: str
    transaction_count: int
    total_amount: float
    percentage: float

class TemporalIndicator(BaseModel):
    type: str
    severity: str
    description: str
    evidence_transaction_ids: List[str]

class TemporalAnalysis(BaseModel):
    transaction_count: int
    time_gaps: TimeGap
    hourly_activity: List[HourlyActivity]
    daily_activity: List[DailyActivity]
    period_activity: List[TimePeriodActivity]
    indicators: List[TemporalIndicator]

# ==============================================================================
# GEOGRAPHIC ANALYSIS
# ==============================================================================

class DistrictActivity(BaseModel):
    district: str
    transaction_count: int
    account_count: int
    total_amount: float

class GeographicTransition(BaseModel):
    previous_transaction_id: str
    current_transaction_id: str
    previous_district: Optional[str]
    current_district: Optional[str]
    distance_km: float
    time_gap_minutes: float
    speed_kmh: Optional[float]

class MovementSummary(BaseModel):
    total_distance_km: float
    average_distance_km: float
    maximum_distance_km: float
    district_transitions: int
    unique_districts: int

class GeographicConcentration(BaseModel):
    dominant_district: str
    dominant_district_percentage: float
    unique_districts: int

class AccountGeography(BaseModel):
    account_count_per_district: Dict[str, int]
    unique_account_districts: int

class GeographicAnalysis(BaseModel):
    district_distribution: List[DistrictActivity]
    account_geography: AccountGeography
    movement_summary: MovementSummary
    transitions: List[GeographicTransition]
    concentration: GeographicConcentration

# ==============================================================================
# WITHDRAWAL CANDIDATES
# ==============================================================================

class WithdrawalCandidateFeature(BaseModel):
    location_id: str
    district: str
    latitude: float
    longitude: float
    distance_from_latest_activity_km: float
    distance_from_terminal_account_km: float
    distance_from_victim_km: float
    district_match_latest_activity: bool
    district_match_terminal_account: bool
    historical_cases_nearby: int

# ==============================================================================
# HISTORICAL COMPARISON
# ==============================================================================

class HistoricalComparison(BaseModel):
    historical_case_id: str
    district: Optional[str]
    city: Optional[str]
    crime_type: str
    distance_from_current_activity_km: float
    withdrawal_location_id: Optional[str]

# ==============================================================================
# FEATURE VECTOR
# ==============================================================================

class TemporalFeatures(BaseModel):
    transaction_count: int
    average_gap_minutes: float
    minimum_gap_minutes: float
    maximum_gap_minutes: float
    night_percentage: float
    evening_percentage: float

class GeographicFeatures(BaseModel):
    unique_districts: int
    district_transitions: int
    total_distance_km: float
    average_distance_km: float
    maximum_distance_km: float

class FeatureVector(BaseModel):
    temporal_features: TemporalFeatures
    geographic_features: GeographicFeatures

# ==============================================================================
# MASTER RESPONSE
# ==============================================================================

class TimeGeographyResponse(BaseModel):
    complaint_id: str
    temporal_analysis: TemporalAnalysis
    geographic_analysis: GeographicAnalysis
    withdrawal_candidate_features: List[WithdrawalCandidateFeature]
    historical_comparison: List[HistoricalComparison]
    feature_vector: FeatureVector

class CandidateFeatureResponse(BaseModel):
    complaint_id: str
    candidates: List[WithdrawalCandidateFeature]

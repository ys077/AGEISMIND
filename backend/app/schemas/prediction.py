from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any

class PredictionFactorSchema(BaseModel):
    factor_name: str
    contribution: float
    direction: str  # "POSITIVE", "NEGATIVE", "NEUTRAL"

    model_config = ConfigDict(from_attributes=True)

class PredictionCandidate(BaseModel):
    rank: int
    location_id: str
    district: str
    location_name: str
    latitude: float
    longitude: float
    probability: float
    priority: str
    factors: List[PredictionFactorSchema] = []

    model_config = ConfigDict(from_attributes=True)

class PredictionResponse(BaseModel):
    complaint_id: str
    model_version: str
    prediction_timestamp: str
    candidate_count: int
    ranked_candidates: List[PredictionCandidate]

class ModelEvaluation(BaseModel):
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    top_1_hit_rate: Optional[float]
    top_3_hit_rate: Optional[float]
    top_5_hit_rate: Optional[float]
    mrr: Optional[float]

class RiskThresholds(BaseModel):
    critical: float
    high: float
    medium: float

class ModelInfoResponse(BaseModel):
    model_type: str
    model_version: str
    training_cases: int
    validation_cases: int
    test_cases: int
    training_rows: int
    feature_count: int
    positive_labels: int
    negative_labels: int
    training_date: str
    dataset_type: str = "SYNTHETIC_PROTOTYPE"
    target_definition: str = "withdrawal_zone"
    disclaimer: str = "Model training and evaluation use synthetic prototype data created for demonstration purposes. Performance metrics do not represent real-world operational accuracy."
    evaluation: ModelEvaluation
    risk_thresholds: RiskThresholds

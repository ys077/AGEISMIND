from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

class ExplanationFactor(BaseModel):
    factor_name: str
    feature_value: Optional[str] = None
    contribution: float
    direction: str
    explanation_text: Optional[str] = None

class CandidateExplanation(BaseModel):
    rank: int
    location_id: str
    district: str
    probability: float
    summary: str
    positive_factors: List[ExplanationFactor]
    negative_factors: List[ExplanationFactor]

class CaseExplanation(BaseModel):
    overall_summary: str
    dominant_features: List[ExplanationFactor]

class ExplainabilityResponse(BaseModel):
    complaint_id: str
    model_version: str
    prediction_timestamp: str
    case_explanation: CaseExplanation
    candidates: List[CandidateExplanation]
    
class GlobalFeatureImportance(BaseModel):
    feature_name: str
    importance: float
    rank: int

class ModelExplainabilityResponse(BaseModel):
    model_version: str
    supported_model_type: str
    explanation_method: str
    global_feature_importance: List[GlobalFeatureImportance]

class SingleCandidateExplanationResponse(BaseModel):
    model_version: str
    candidate: CandidateExplanation

import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Prediction, PredictionFactor, WithdrawalLocation
from app.ml.model_loader import model_loader
from app.schemas.explainability import (
    ExplainabilityResponse,
    CaseExplanation,
    CandidateExplanation,
    ExplanationFactor,
    ModelExplainabilityResponse,
    GlobalFeatureImportance,
    SingleCandidateExplanationResponse
)

def _build_candidate_explanation(pred: Prediction) -> CandidateExplanation:
    pos_factors = []
    neg_factors = []
    
    for f in pred.factors:
        ef = ExplanationFactor(
            factor_name=f.factor_name,
            feature_value=f.feature_value,
            contribution=float(f.contribution),
            direction=f.direction,
            explanation_text=f.explanation_text
        )
        if f.direction == "POSITIVE":
            pos_factors.append(ef)
        elif f.direction == "NEGATIVE":
            neg_factors.append(ef)
            
    # Sort by absolute contribution
    pos_factors.sort(key=lambda x: x.contribution, reverse=True)
    neg_factors.sort(key=lambda x: abs(x.contribution), reverse=True)
    
    # Take top N
    top_pos = pos_factors[:5]
    top_neg = neg_factors[:3]
    
    summary_parts = []
    if top_pos:
        summary_parts.append(f"The most significant positive factor was: {top_pos[0].explanation_text}")
    if top_neg:
        summary_parts.append(f"However, its score was reduced because: {top_neg[0].explanation_text}")
        
    summary = " ".join(summary_parts) if summary_parts else "No significant factors found."
    
    return CandidateExplanation(
        rank=pred.rank,
        location_id=pred.location_id,
        district=pred.withdrawal_loc.district_id,
        probability=float(pred.risk_score),
        summary=summary,
        positive_factors=top_pos,
        negative_factors=top_neg
    )

def get_case_explanation(complaint_id: str, db: Session) -> ExplainabilityResponse:
    preds = db.query(Prediction).filter(Prediction.complaint_id == complaint_id).order_by(Prediction.rank).all()
    if not preds:
        raise HTTPException(status_code=404, detail="No predictions found for this complaint. Please generate predictions first.")
        
    metadata = model_loader.get_metadata()
    if preds[0].model_version != metadata["model_version"]:
        raise HTTPException(status_code=400, detail="Prediction model version mismatch. Please regenerate predictions.")
        
    candidates = [_build_candidate_explanation(p) for p in preds]
    
    # Case level dominant features: aggregate positive contributions across top 5 candidates
    feature_aggs = {}
    for c in candidates[:5]:
        for f in c.positive_factors:
            feature_aggs[f.factor_name] = feature_aggs.get(f.factor_name, 0) + f.contribution
            
    sorted_aggs = sorted(feature_aggs.items(), key=lambda x: x[1], reverse=True)
    top_global_features = []
    
    for fname, agg_contrib in sorted_aggs[:3]:
        top_global_features.append(ExplanationFactor(
            factor_name=fname,
            contribution=agg_contrib,
            direction="POSITIVE",
            explanation_text=f"Globally across top candidates, {fname} was a dominant driving factor."
        ))
        
    case_exp = CaseExplanation(
        overall_summary="The model's ranking was primarily driven by geographic proximity and historical activity patterns across the top candidates.",
        dominant_features=top_global_features
    )
    
    return ExplainabilityResponse(
        complaint_id=complaint_id,
        model_version=metadata["model_version"],
        prediction_timestamp=preds[0].created_at.isoformat(),
        case_explanation=case_exp,
        candidates=candidates
    )

def get_candidate_explanation(complaint_id: str, location_id: str, db: Session) -> SingleCandidateExplanationResponse:
    pred = db.query(Prediction).filter(
        Prediction.complaint_id == complaint_id,
        Prediction.location_id == location_id
    ).first()
    
    if not pred:
        return None
        
    metadata = model_loader.get_metadata()
    if pred.model_version != metadata["model_version"]:
        raise HTTPException(status_code=400, detail="Prediction model version mismatch.")
        
    cand_exp = _build_candidate_explanation(pred)
    
    return SingleCandidateExplanationResponse(
        model_version=metadata["model_version"],
        candidate=cand_exp
    )

def get_global_explainability_info() -> ModelExplainabilityResponse:
    metadata = model_loader.get_metadata()
    model = model_loader.get_model()
    
    global_fi_dict = metadata.get("global_feature_importance", {})
    
    global_fi = []
    for fname in metadata["features"]:
        importance = global_fi_dict.get(fname, 0.0)
        global_fi.append({
            "feature_name": fname,
            "importance": importance
        })
        
    # Sort by importance descending
    global_fi.sort(key=lambda x: x["importance"], reverse=True)
    
    # Assign ranks and convert to objects
    ranked_global_fi = []
    for i, item in enumerate(global_fi):
        ranked_global_fi.append(GlobalFeatureImportance(
            feature_name=item["feature_name"],
            importance=item["importance"],
            rank=i+1
        ))
        
    return ModelExplainabilityResponse(
        model_version=metadata["model_version"],
        supported_model_type=metadata["model_type"],
        explanation_method="SHAP Explainer (Global approximation from evaluation data)",
        global_feature_importance=ranked_global_fi
    )

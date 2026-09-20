import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models import Complaint, Transaction, Account, WithdrawalLocation
from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_loader import model_loader
from app.services.risk_service import get_risk_level

def generate_prediction(
    db: Session,
    complaint: Complaint,
    transactions: List[Transaction],
    accounts: List[Account],
    candidates: List[WithdrawalLocation],
    job_id: str = None,
    update_job_stage=None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generates predictions for all candidates against a complaint.
    Returns:
    - Ranked list of candidate dictionaries.
    - Model metadata used.
    """
    model = model_loader.get_model()
    metadata = model_loader.get_metadata()
    
    expected_features = metadata["features"]
    hist_freq = metadata.get("historical_frequencies", {})
    
    fe = FeatureEngineer(db)
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "TRANSACTION_FEATURES")
        
    # Generate features
    df = fe.generate_features_for_complaint(
        complaint=complaint,
        transactions=transactions,
        accounts=accounts,
        candidates=candidates,
        historical_frequencies=hist_freq
    )
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "NETWORK_FEATURES")
        
    # Removed artificial temporal delay for visibility as feature generation is fast
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "GEOGRAPHIC_FEATURES")
        
    # Validate feature alignment
    missing_cols = set(expected_features) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Feature schema mismatch. Missing: {missing_cols}")
        
    X = df[expected_features]
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "ML_MODEL_EVALUATION")
        
    # Predict probabilities
    probs = model.predict_proba(X)[:, 1]
    
    from app.ml.explainer import explain_predictions
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "SHAP_EXPLANATION")
    
    # Generate SHAP explanations
    all_candidate_factors = explain_predictions(df, expected_features)
    
    # Attach probabilities back to candidate info
    results = []
    
    if update_job_stage and job_id:
        update_job_stage(job_id, "RISK_CLASSIFICATION")
        
    for idx, candidate in enumerate(candidates):
        dist = float(df.loc[idx, "dist_from_complaint_deg"])
        prob = float(probs[idx])
        
        priority = get_risk_level(prob)
            
        factors = all_candidate_factors[idx]
            
        results.append({
            "candidate": candidate,
            "probability": prob,
            "dist": dist,
            "priority": priority,
            "factors": factors
        })
        
    # Rank candidates (Probability DESC, Distance ASC, ID ASC)
    results.sort(key=lambda x: (-x["probability"], x["dist"], x["candidate"].location_id))
    
    # Assign ranks
    ranked_results = []
    for rank, res in enumerate(results, start=1):
        ranked_results.append({
            "rank": rank,
            "location_id": res["candidate"].location_id,
            "district": res["candidate"].district_id,
            "location_name": res["candidate"].location_name,
            "latitude": float(res["candidate"].latitude),
            "longitude": float(res["candidate"].longitude),
            "probability": res["probability"],
            "priority": res["priority"],
            "factors": res["factors"]
        })
        
    return ranked_results, metadata

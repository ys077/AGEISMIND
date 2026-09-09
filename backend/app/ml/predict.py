import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models import Complaint, Transaction, Account, WithdrawalLocation
from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_loader import model_loader

def generate_prediction(
    db: Session,
    complaint: Complaint,
    transactions: List[Transaction],
    accounts: List[Account],
    candidates: List[WithdrawalLocation]
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
    
    # Generate features
    df = fe.generate_features_for_complaint(
        complaint=complaint,
        transactions=transactions,
        accounts=accounts,
        candidates=candidates,
        historical_frequencies=hist_freq
    )
    
    # Validate feature alignment
    missing_cols = set(expected_features) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Feature schema mismatch. Missing: {missing_cols}")
        
    X = df[expected_features]
    
    # Predict probabilities
    probs = model.predict_proba(X)[:, 1]
    
    # Attach probabilities back to candidate info
    results = []
    for idx, candidate in enumerate(candidates):
        dist = float(df.loc[idx, "dist_from_complaint_deg"])
        prob = float(probs[idx])
        
        # Determine priority string based on prob
        if prob > 0.8:
            priority = "CRITICAL"
        elif prob > 0.5:
            priority = "HIGH"
        elif prob > 0.2:
            priority = "MEDIUM"
        else:
            priority = "LOW"
            
        # Top 3 feature values to save as explanations (simple feature importance heuristic for now)
        # For tree models, we might extract shap values later, but for now we just store the raw values of key geographic factors
        factors = [
            {"factor_name": "dist_from_complaint_deg", "contribution": dist, "direction": "NEGATIVE" if dist > 0 else "NEUTRAL"},
            {"factor_name": "same_district_as_victim", "contribution": float(df.loc[idx, "same_district_as_victim"]), "direction": "POSITIVE"},
            {"factor_name": "historical_frequency", "contribution": float(df.loc[idx, "historical_frequency"]), "direction": "POSITIVE"}
        ]
            
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

import shap
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from app.ml.model_loader import model_loader

FEATURE_DESCRIPTIONS = {
    "amount": "Reported fraud amount",
    "tx_count": "Total number of transactions",
    "successful_tx_count": "Number of successful transactions",
    "total_amount": "Total amount transferred",
    "avg_amount": "Average transaction amount",
    "max_amount": "Maximum transaction amount",
    "min_amount": "Minimum transaction amount",
    "unique_senders": "Number of unique sender accounts",
    "unique_receivers": "Number of unique receiver accounts",
    "is_upi": "Presence of UPI transactions",
    "is_phishing": "Phishing modus operandi",
    "is_sim_swap": "SIM swap modus operandi",
    "is_job": "Job fraud modus operandi",
    "is_investment": "Investment fraud modus operandi",
    "is_card": "Card fraud modus operandi",
    "avg_tx_gap": "Average time gap between transactions",
    "max_tx_gap": "Maximum time gap between transactions",
    "min_tx_gap": "Minimum time gap between transactions",
    "night_pct": "Percentage of activity during night hours (00:00-06:00)",
    "morning_pct": "Percentage of activity during morning hours (06:00-12:00)",
    "afternoon_pct": "Percentage of activity during afternoon hours (12:00-18:00)",
    "evening_pct": "Percentage of activity during evening hours (18:00-24:00)",
    "candidate_atm_count": "Number of ATMs in the candidate area",
    "candidate_area_risk": "Baseline risk level of the candidate area",
    "dist_from_complaint_deg": "Geographic distance from the victim's core location",
    "same_district_as_victim": "Candidate is in the same district as the victim",
    "same_district_as_terminal": "Candidate is in the same district as the terminal account",
    "historical_frequency": "Historical frequency of withdrawals at this candidate location"
}

def _format_feature_value(feature_name: str, raw_value: Any) -> str:
    if pd.isna(raw_value):
        return "Unknown"
    val = float(raw_value)
    if feature_name.startswith("is_") or feature_name.startswith("same_district"):
        return "Yes" if val > 0.5 else "No"
    if feature_name.endswith("_pct"):
        return f"{val:.1f}%"
    if feature_name == "dist_from_complaint_deg":
        km = val * 111.0
        return f"{km:.1f} km"
    if "amount" in feature_name:
        return f"₹{val:,.2f}"
    if feature_name.endswith("_tx_gap"):
        return f"{val:.1f} min"
    if feature_name.endswith("count") or feature_name == "historical_frequency" or feature_name == "candidate_area_risk":
        return str(int(val))
    return f"{val:.2f}"

def _generate_explanation_text(feature_name: str, value_str: str, contribution: float) -> str:
    desc = FEATURE_DESCRIPTIONS.get(feature_name, feature_name.replace("_", " ").capitalize())
    if contribution > 0:
        return f"{desc} ({value_str}) contributed positively to the model score."
    elif contribution < 0:
        return f"{desc} ({value_str}) was associated with a lower model score."
    else:
        return f"{desc} ({value_str}) had a neutral effect."

def explain_predictions(df: pd.DataFrame, expected_features: List[str]) -> List[List[Dict[str, Any]]]:
    model = model_loader.get_model()
    X = df[expected_features]
    
    imputer = model.named_steps['imputer']
    clf = model.named_steps['clf']
    
    X_imputed = imputer.transform(X)
    
    # To keep it fast and compatible, we use shap.Explainer
    # We use a zero background dataset to ensure we get non-zero SHAP values
    background = np.zeros((1, X_imputed.shape[1]))
    explainer = shap.KernelExplainer(clf.predict_proba, background)
    shap_values = explainer.shap_values(X_imputed)
    
    if isinstance(shap_values, list):
        sv = shap_values[1]
    elif len(shap_values.shape) == 3:
        sv = shap_values[:, :, 1]
    else:
        sv = shap_values
        
    all_candidate_factors = []
    for i in range(len(X)):
        candidate_factors = []
        for j, feature_name in enumerate(expected_features):
            raw_val = X.iloc[i][feature_name]
            contribution = float(sv[i, j])
            
            if abs(contribution) < 0.00001:
                continue
                
            direction = "POSITIVE" if contribution > 0 else "NEGATIVE"
            val_str = _format_feature_value(feature_name, raw_val)
            exp_text = _generate_explanation_text(feature_name, val_str, contribution)
            
            candidate_factors.append({
                "factor_name": feature_name,
                "feature_value": val_str,
                "contribution": contribution,
                "direction": direction,
                "explanation_text": exp_text
            })
            
        candidate_factors.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        all_candidate_factors.append(candidate_factors)
        
    return all_candidate_factors

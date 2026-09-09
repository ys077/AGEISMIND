import pandas as pd
import numpy as np
import datetime
import json
import joblib
from sqlalchemy.orm import Session
from sklearn.model_selection import GroupShuffleSplit
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from app.models import HistoricalCase, WithdrawalLocation
from app.ml.feature_engineering import FeatureEngineer
from app.ml.evaluation import evaluate_predictions
from app.ml.model_loader import MODEL_PATH, METADATA_PATH, MODEL_DIR

def build_training_dataset(db: Session) -> pd.DataFrame:
    """Extracts all historical cases and candidate locations, then generates features."""
    cases = db.query(HistoricalCase).all()
    candidates = db.query(WithdrawalLocation).all()
    
    fe = FeatureEngineer(db)
    
    # Need to split cases beforehand to prevent historical_frequency leakage?
    # Better: compute frequencies only from the training split. We will do this properly.
    
    return cases, candidates, fe

def train_model(db: Session):
    """
    Full training pipeline:
    1. Load data
    2. Group split
    3. Calculate historical frequencies from train split only
    4. Feature generation
    5. Baseline & Candidate Model training
    6. Evaluation & Selection
    7. Save
    """
    cases, candidates, fe = build_training_dataset(db)
    
    if not cases:
        raise ValueError("No historical cases found for training.")
        
    case_ids = [c.historical_case_id for c in cases]
    
    # 1. Group split (70% train, 30% val/test)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_idx, test_val_idx = next(gss.split(cases, groups=case_ids))
    
    train_cases = [cases[i] for i in train_idx]
    test_val_cases = [cases[i] for i in test_val_idx]
    
    # Split test_val into validation (15%) and test (15%)
    test_val_case_ids = [c.historical_case_id for c in test_val_cases]
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
    val_idx, test_idx = next(gss2.split(test_val_cases, groups=test_val_case_ids))
    
    val_cases = [test_val_cases[i] for i in val_idx]
    test_cases = [test_val_cases[i] for i in test_idx]
    
    # 2. Compute historical frequencies ONLY from training cases (leakage prevention)
    hist_freq = {}
    for c in train_cases:
        wz = c.withdrawal_zone
        hist_freq[wz] = hist_freq.get(wz, 0) + 1
        
    # 3. Generate Features
    print("Generating training features...")
    df_train = pd.concat([fe.generate_features_for_historical_case(c, candidates, hist_freq) for c in train_cases], ignore_index=True)
    
    print("Generating validation features...")
    df_val = pd.concat([fe.generate_features_for_historical_case(c, candidates, hist_freq) for c in val_cases], ignore_index=True)
    
    print("Generating test features...")
    df_test = pd.concat([fe.generate_features_for_historical_case(c, candidates, hist_freq) for c in test_cases], ignore_index=True)
    
    # Combine train and val for actual model fitting (using CV or early stopping conceptually, though here we'll just train on train+val)
    df_fit = pd.concat([df_train, df_val], ignore_index=True)
    
    # Feature columns (exclude identifiers and target)
    drop_cols = ["historical_case_id", "candidate_location_id", "district_id", "is_target"]
    feature_cols = [c for c in df_fit.columns if c not in drop_cols]
    
    X_fit = df_fit[feature_cols]
    y_fit = df_fit["is_target"]
    groups_fit = df_fit["historical_case_id"]
    
    X_test = df_test[feature_cols]
    y_test = df_test["is_target"]
    groups_test = df_test["historical_case_id"]
    
    # Check leakage
    if "is_target" in feature_cols or "withdrawal_zone" in feature_cols:
        raise ValueError("Data leakage detected! Target column included in features.")
        
    overlap = set(df_fit["historical_case_id"]).intersection(set(df_test["historical_case_id"]))
    if overlap:
        raise ValueError(f"Data leakage detected! Overlapping cases in train and test sets: {overlap}")
        
    # 4. Train Models
    print("Training Logistic Regression (Baseline)...")
    lr_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(class_weight='balanced', random_state=42, max_iter=1000))
    ])
    lr_pipeline.fit(X_fit, y_fit)
    
    print("Training HistGradientBoosting...")
    hgb_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        # HGB doesn't strictly need scaling, but it's safe.
        ('clf', HistGradientBoostingClassifier(class_weight='balanced', random_state=42, max_iter=200))
    ])
    hgb_pipeline.fit(X_fit, y_fit)
    
    # 5. Evaluate
    lr_probs = lr_pipeline.predict_proba(X_test)[:, 1]
    hgb_probs = hgb_pipeline.predict_proba(X_test)[:, 1]
    
    lr_metrics = evaluate_predictions(y_test.values, lr_probs, groups_test.values)
    hgb_metrics = evaluate_predictions(y_test.values, hgb_probs, groups_test.values)
    
    # Select best model based on Top-3 Hit Rate (ranking is what we care about)
    if hgb_metrics["top_3_hit_rate"] >= lr_metrics["top_3_hit_rate"]:
        best_model = hgb_pipeline
        best_metrics = hgb_metrics
        model_type = "HistGradientBoostingClassifier"
    else:
        best_model = lr_pipeline
        best_metrics = lr_metrics
        model_type = "LogisticRegression"
        
    # 6. Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    
    metadata = {
        "model_version": "withdrawal_model_v1",
        "model_type": model_type,
        "training_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "feature_count": len(feature_cols),
        "features": feature_cols,
        "historical_frequencies": hist_freq,
        "metrics": best_metrics,
        "dataset_stats": {
            "training_cases": len(train_cases),
            "validation_cases": len(val_cases),
            "test_cases": len(test_cases),
            "training_rows": len(df_fit),
            "positive_labels": int(y_fit.sum()),
            "negative_labels": int(len(y_fit) - y_fit.sum()),
        }
    }
    
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    return metadata, lr_metrics, hgb_metrics

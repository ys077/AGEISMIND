import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Complaint, Transaction, Account, WithdrawalLocation, Prediction, PredictionFactor
from app.ml.predict import generate_prediction
from app.ml.model_loader import model_loader
from app.schemas.prediction import PredictionResponse, ModelInfoResponse, ModelEvaluation

def generate_and_save_prediction(complaint_id: str, db: Session) -> PredictionResponse:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise ValueError(f"Complaint {complaint_id} not found")
        
    transactions = db.query(Transaction).filter(Transaction.complaint_id == complaint_id).all()
    
    # Get all distinct accounts involved in transactions
    account_ids = set()
    for tx in transactions:
        account_ids.add(tx.sender_account)
        account_ids.add(tx.receiver_account)
    accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
    
    candidates = db.query(WithdrawalLocation).all()
    if not candidates:
        raise ValueError("No withdrawal candidates found in database.")
        
    # Generate predictions
    ranked_results, metadata = generate_prediction(db, complaint, transactions, accounts, candidates)
    
    # Persist to database (clear old predictions for this complaint first)
    db.query(Prediction).filter(Prediction.complaint_id == complaint_id).delete()
    db.flush()
    
    prediction_models = []
    
    for res in ranked_results:
        # Create Prediction record
        pred = Prediction(
            prediction_id=uuid.uuid4(),
            complaint_id=complaint_id,
            location_id=res["location_id"],
            risk_score=res["probability"],
            priority=res["priority"],
            rank=res["rank"],
            model_version=metadata["model_version"]
        )
        db.add(pred)
        prediction_models.append(pred)
        
        # Create PredictionFactor records
        for factor in res["factors"]:
            pf = PredictionFactor(
                prediction_id=pred.prediction_id,
                factor_name=factor["factor_name"],
                contribution=factor["contribution"],
                direction=factor["direction"],
                feature_value=factor.get("feature_value"),
                explanation_text=factor.get("explanation_text")
            )
            db.add(pf)
            
    db.commit()
    
    # We use the timestamp of the top prediction as the overall timestamp
    timestamp = prediction_models[0].created_at.isoformat() if prediction_models else ""
    
    return PredictionResponse(
        complaint_id=complaint_id,
        model_version=metadata["model_version"],
        prediction_timestamp=timestamp,
        candidate_count=len(ranked_results),
        ranked_candidates=ranked_results
    )

def get_stored_prediction(complaint_id: str, db: Session, top_k: int = None) -> PredictionResponse:
    # Check if we have predictions
    preds = db.query(Prediction).filter(Prediction.complaint_id == complaint_id).order_by(Prediction.rank).all()
    
    if not preds:
        return None
        
    if top_k is not None:
        preds = preds[:top_k]
        
    ranked_candidates = []
    for p in preds:
        loc = p.withdrawal_loc
        factors = [
            {
                "factor_name": f.factor_name,
                "contribution": float(f.contribution),
                "direction": f.direction,
                "feature_value": f.feature_value,
                "explanation_text": f.explanation_text
            }
            for f in p.factors
        ]
        
        ranked_candidates.append({
            "rank": p.rank,
            "location_id": p.location_id,
            "district": loc.district_id,
            "location_name": loc.location_name,
            "latitude": float(loc.latitude),
            "longitude": float(loc.longitude),
            "probability": float(p.risk_score),
            "priority": p.priority,
            "factors": factors
        })
        
    return PredictionResponse(
        complaint_id=complaint_id,
        model_version=preds[0].model_version,
        prediction_timestamp=preds[0].created_at.isoformat(),
        candidate_count=len(preds),
        ranked_candidates=ranked_candidates
    )

def get_model_info() -> ModelInfoResponse:
    metadata = model_loader.get_metadata()
    
    eval_metrics = ModelEvaluation(
        roc_auc=metadata["metrics"]["roc_auc"],
        pr_auc=metadata["metrics"]["pr_auc"],
        precision=metadata["metrics"]["precision"],
        recall=metadata["metrics"]["recall"],
        f1_score=metadata["metrics"]["f1_score"],
        top_1_hit_rate=metadata["metrics"]["top_1_hit_rate"],
        top_3_hit_rate=metadata["metrics"]["top_3_hit_rate"],
        top_5_hit_rate=metadata["metrics"]["top_5_hit_rate"],
        mrr=metadata["metrics"]["mrr"]
    )
    
    return ModelInfoResponse(
        model_type=metadata["model_type"],
        model_version=metadata["model_version"],
        training_cases=metadata["dataset_stats"]["training_cases"],
        validation_cases=metadata["dataset_stats"]["validation_cases"],
        test_cases=metadata["dataset_stats"]["test_cases"],
        training_rows=metadata["dataset_stats"]["training_rows"],
        feature_count=metadata["feature_count"],
        positive_labels=metadata["dataset_stats"]["positive_labels"],
        negative_labels=metadata["dataset_stats"]["negative_labels"],
        training_date=metadata["training_date"],
        evaluation=eval_metrics
    )

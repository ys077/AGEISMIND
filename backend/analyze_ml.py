import asyncio
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath('d:/ADMIN/Music/Projects/SIH - AGEISMIND/backend'))

from app.ml.predict import generate_prediction
from app.ml.feature_engineering import FeatureEngineer
from app.ml.model_loader import model_loader
from app.db.database import SessionLocal
from app.models import Complaint, WithdrawalLocation, Transaction, Account

def analyze():
    db = SessionLocal()
    complaints = ["CC1001", "CC1002", "CC1003", "CC1004", "CC1005"]
    model, metadata = model_loader.load_model()
    expected_features = metadata["features"]
    
    print("--- ML DIAGNOSTIC REPORT ---")
    
    for cid in complaints:
        try:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == cid).first()
            if not complaint:
                print(f"{cid}: Not found in DB")
                continue
            
            transactions = db.query(Transaction).filter(Transaction.complaint_id == cid).all()
            account_ids = set()
            for tx in transactions:
                account_ids.add(tx.sender_account)
                account_ids.add(tx.receiver_account)
            accounts = db.query(Account).filter(Account.account_id.in_(account_ids)).all()
            
            candidates = db.query(WithdrawalLocation).all()
            
            fe = FeatureEngineer(db)
            hist_freq = metadata.get("historical_frequencies", {})
            df = fe.generate_features_for_complaint(complaint, transactions, accounts, candidates, hist_freq)
            
            X = df[expected_features]
            
            unique_vectors = len(X.drop_duplicates())
            print(f"Complaint: {cid}")
            print(f"Candidates: {len(candidates)}")
            print(f"Feature-vector uniqueness: {unique_vectors} / {len(candidates)}")
            
            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(X)[:, 1]
            else:
                probs = model.predict(X)
                
            unique_probs = len(np.unique(probs))
            print(f"Unique probability count: {unique_probs}")
            print(f"Min: {np.min(probs):.4f}")
            print(f"Max: {np.max(probs):.4f}")
            print(f"Mean: {np.mean(probs):.4f}")
            print(f"Std Dev: {np.std(probs):.4f}")
            
            top_idx = np.argmax(probs)
            print(f"Top candidate ID: {candidates[top_idx].location_id}")
            print(f"Top probability: {probs[top_idx]:.4f}")
            
            print("-" * 30)
            
        except Exception as e:
            print(f"Error on {cid}: {e}")
            import traceback
            traceback.print_exc()
            
    db.close()

if __name__ == '__main__':
    analyze()

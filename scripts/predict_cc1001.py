"""
Generate predictions for CC1001 only to save time for demonstration.
"""

import sys
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.api.deps import SessionLocal
from app.models.complaint import Complaint
from app.services.prediction_service import generate_and_save_prediction
from app.services.alert_service import generate_alerts_from_predictions

def main():
    print("===============================================")
    print("  PREDICTION GENERATION FOR CC1001")
    print("===============================================")
    
    db = SessionLocal()
    try:
        complaint = db.query(Complaint).filter(Complaint.complaint_id == "CC1001").first()
        if not complaint:
            print("CC1001 not found!")
            return
            
        print("Found CC1001. Starting prediction generation...")
        
        generate_and_save_prediction(complaint.complaint_id, db)
        
        print("\nPrediction Generation Complete for CC1001.")
        
        print("\nGenerating alerts for predictions...")
        alerts_created = generate_alerts_from_predictions(db)
        print(f"Successfully created {alerts_created} new alerts.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

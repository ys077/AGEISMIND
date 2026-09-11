"""
Bulk prediction and alert generator.
Iterates through all complaints in the database and generates predictions using the ML model.
Then generates alerts for the high/medium priority predictions.
"""

import sys
from pathlib import Path
import traceback

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.api.deps import SessionLocal
from app.models.complaint import Complaint
from app.services.prediction_service import generate_and_save_prediction
from app.services.alert_service import generate_alerts_from_predictions

def main():
    print("===============================================")
    print("  BULK PREDICTION & ALERT GENERATION")
    print("===============================================")
    
    db = SessionLocal()
    try:
        all_complaints = db.query(Complaint).all()
        # Filter CC1001 to ensure it's included, and take 24 others
        cc1001 = [c for c in all_complaints if c.complaint_id == "CC1001"]
        others = [c for c in all_complaints if c.complaint_id != "CC1001"][:24]
        complaints = cc1001 + others
        
        total = len(complaints)
        print(f"Found {total} complaints. Starting prediction generation...")
        
        success = 0
        failed = 0
        
        for i, c in enumerate(complaints):
            try:
                generate_and_save_prediction(c.complaint_id, db)
                success += 1
                if success % 100 == 0:
                    print(f"  [{success}/{total}] Predictions generated...")
            except Exception as e:
                failed += 1
                print(f"  [ERROR] Failed on {c.complaint_id}: {str(e)}")
                # traceback.print_exc()
                
        print(f"\nPrediction Generation Complete: {success} successful, {failed} failed.")
        
        print("\nGenerating alerts for predictions...")
        alerts_created = generate_alerts_from_predictions(db)
        print(f"Successfully created {alerts_created} new alerts.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()

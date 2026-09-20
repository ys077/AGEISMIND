import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db.database import SessionLocal
from app.models.complaint import Complaint
from app.services.prediction_service import start_prediction_job, PREDICTION_JOBS
import time

db = SessionLocal()
comp = db.query(Complaint).first()
if not comp:
    print("No complaints in DB!")
    sys.exit(1)
    
print("Found complaint:", comp.complaint_id)
job_id = start_prediction_job(comp.complaint_id)
print("Job ID:", job_id)
for i in range(10):
    time.sleep(0.5)
    print("Status:", PREDICTION_JOBS.get(job_id))
    if PREDICTION_JOBS.get(job_id, {}).get("status") in ["COMPLETED", "FAILED"]:
        break

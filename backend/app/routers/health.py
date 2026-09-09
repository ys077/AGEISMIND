from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Check DB connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "cybercrime-prediction-api"
        }
    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "service": "cybercrime-prediction-api"
        }

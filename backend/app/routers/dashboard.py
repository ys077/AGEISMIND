from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_db
from app.models.complaint import Complaint
from app.services import alert_service

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/overview", response_model=Dict[str, Any])
def get_dashboard_overview(db: Session = Depends(get_db)):
    """
    Get comprehensive executive dashboard data including total complaints,
    financial exposure, crime categories, fraud types, district rankings, and recent cases.
    """
    # 1. Macro KPIs
    total_complaints = db.query(Complaint).count()
    total_fraud_val = db.query(func.sum(Complaint.fraud_amount)).scalar() or 0
    total_fraud_amount = float(total_fraud_val)
    avg_fraud_amount = round(total_fraud_amount / total_complaints, 2) if total_complaints > 0 else 0

    # Status Breakdown
    statuses_raw = db.query(
        Complaint.status, 
        func.count(Complaint.complaint_id)
    ).group_by(Complaint.status).all()
    status_breakdown = {s[0] or "Unknown": s[1] for s in statuses_raw}

    # 2. Crime Category Breakdown
    cat_query = db.query(
        Complaint.crime_category,
        func.count(Complaint.complaint_id),
        func.sum(Complaint.fraud_amount)
    ).group_by(Complaint.crime_category).order_by(desc(func.count(Complaint.complaint_id))).all()

    categories_breakdown = []
    for cat, count, amt in cat_query:
        amt_float = float(amt) if amt else 0
        categories_breakdown.append({
            "category": cat or "Uncategorized",
            "count": count,
            "amount": amt_float,
            "percentage": round((amt_float / total_fraud_amount * 100), 1) if total_fraud_amount > 0 else 0
        })

    # 3. Fraud Typology Breakdown
    type_query = db.query(
        Complaint.fraud_type,
        func.count(Complaint.complaint_id),
        func.sum(Complaint.fraud_amount)
    ).group_by(Complaint.fraud_type).order_by(desc(func.count(Complaint.complaint_id))).limit(10).all()

    fraud_types_breakdown = []
    for ftype, count, amt in type_query:
        fraud_types_breakdown.append({
            "fraud_type": ftype or "Other",
            "count": count,
            "amount": float(amt) if amt else 0
        })

    # 4. Top Hotspot Districts / Cities
    city_query = db.query(
        Complaint.victim_city,
        Complaint.district_id,
        func.count(Complaint.complaint_id),
        func.sum(Complaint.fraud_amount)
    ).group_by(Complaint.victim_city, Complaint.district_id).order_by(desc(func.count(Complaint.complaint_id))).limit(8).all()

    districts_ranking = []
    for city, dist_id, count, amt in city_query:
        amt_float = float(amt) if amt else 0
        risk_level = "CRITICAL" if count >= 33 else "HIGH" if count >= 30 else "ELEVATED"
        districts_ranking.append({
            "city": city or "Unknown",
            "district_id": dist_id or "TN00",
            "complaint_count": count,
            "total_fraud_amount": amt_float,
            "risk_level": risk_level
        })

    # 5. Source Channel Distribution
    channel_query = db.query(
        Complaint.source_channel,
        func.count(Complaint.complaint_id)
    ).group_by(Complaint.source_channel).all()
    channel_breakdown = [{"channel": ch or "Unknown", "count": count} for ch, count in channel_query]

    # 6. Recent Incident Stream (Latest 8 complaints)
    recent_records = db.query(Complaint).order_by(desc(Complaint.complaint_date), desc(Complaint.complaint_time)).limit(8).all()
    recent_complaints = []
    for c in recent_records:
        recent_complaints.append({
            "complaint_id": c.complaint_id,
            "complaint_date": str(c.complaint_date),
            "complaint_time": str(c.complaint_time) if c.complaint_time else None,
            "crime_category": c.crime_category,
            "fraud_type": c.fraud_type,
            "fraud_amount": float(c.fraud_amount) if c.fraud_amount else 0,
            "victim_city": c.victim_city,
            "district_id": c.district_id,
            "source_channel": c.source_channel,
            "status": c.status
        })

    # 7. Alert Intelligence Summary
    alert_summary = alert_service.get_alert_summary(db)

    return {
        "total_complaints": total_complaints,
        "total_fraud_amount": total_fraud_amount,
        "avg_fraud_amount": avg_fraud_amount,
        "status_breakdown": status_breakdown,
        "categories_breakdown": categories_breakdown,
        "fraud_types_breakdown": fraud_types_breakdown,
        "districts_ranking": districts_ranking,
        "channel_breakdown": channel_breakdown,
        "recent_complaints": recent_complaints,
        "alert_summary": alert_summary
    }

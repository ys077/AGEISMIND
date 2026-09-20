from typing import List
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload, noload
from sqlalchemy import func

from app.models.prediction import Prediction
from app.services.risk_service import get_risk_level
from app.models.withdrawal_location import WithdrawalLocation
from app.models.district import District
from app.models.complaint import Complaint
from app.schemas.risk_heatmap import HeatmapCandidate, HeatmapResponse, DistrictAggregation, DistrictHeatmapResponse, GlobalHeatmapResponse, GlobalHeatmapCandidate

_global_heatmap_cache = {}
_CACHE_TTL_SECONDS = 60


def get_global_heatmap(db: Session) -> GlobalHeatmapResponse:
    now = datetime.now()
    cached = _global_heatmap_cache.get("data")
    cached_at = _global_heatmap_cache.get("timestamp")
    if cached is not None and cached_at and now - cached_at < timedelta(seconds=_CACHE_TTL_SECONDS):
        return cached

    rows = (
        db.query(
            WithdrawalLocation.location_id,
            WithdrawalLocation.latitude,
            WithdrawalLocation.longitude,
            District.district_name,
            func.count(func.distinct(Prediction.complaint_id)),
            func.count(Prediction.prediction_id),
            func.avg(Prediction.risk_score),
            func.max(Prediction.risk_score),
        )
        .select_from(Prediction)
        .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
        .join(District, WithdrawalLocation.district_id == District.district_id)
        .group_by(
            WithdrawalLocation.location_id,
            WithdrawalLocation.latitude,
            WithdrawalLocation.longitude,
            District.district_name,
        )
        .all()
    )

    candidates = []
    for loc_id, lat, lng, dist_name, complaint_count, prediction_count, avg_prob, max_prob in rows:
        max_p = float(max_prob or 0)
        candidates.append(GlobalHeatmapCandidate(
            location_id=loc_id,
            latitude=float(lat) if lat is not None else 0.0,
            longitude=float(lng) if lng is not None else 0.0,
            district=dist_name or "Unknown",
            complaint_count=int(complaint_count or 0),
            prediction_count=int(prediction_count or 0),
            average_probability=float(avg_prob or 0),
            maximum_probability=max_p,
            risk_level=get_risk_level(max_p)
        ))

    candidates.sort(key=lambda x: (-x.maximum_probability, x.location_id))
    result = GlobalHeatmapResponse(candidates=candidates)
    _global_heatmap_cache["data"] = result
    _global_heatmap_cache["timestamp"] = now
    return result

def get_heatmap_candidates(complaint_id: str, db: Session, limit: int = 10) -> HeatmapResponse:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    predictions = (
        db.query(Prediction, WithdrawalLocation)
        .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
        .options(
            joinedload(WithdrawalLocation.district),
            noload(WithdrawalLocation.historical_cases),
            noload(WithdrawalLocation.predictions),
            noload(Prediction.factors),
        )
        .filter(Prediction.complaint_id == complaint_id)
        .order_by(Prediction.rank.asc())
        .limit(limit)
        .all()
    )

    if not predictions:
        return HeatmapResponse(complaint_id=complaint_id, candidates=[])

    candidates = []
    for pred, loc in predictions:
        candidates.append(HeatmapCandidate(
            prediction_id=str(pred.prediction_id),
            withdrawal_location_id=loc.location_id,
            latitude=loc.latitude,
            longitude=loc.longitude,
            district=loc.district.district_name if loc.district else loc.district_id,
            probability=float(pred.risk_score),
            rank=pred.rank,
            priority=pred.priority,
            model_version=pred.model_version,
            source=loc.source,
            source_id=loc.source_id,
            operator=loc.operator,
            brand=loc.brand,
            address=loc.address
        ))

    return HeatmapResponse(
        complaint_id=complaint_id,
        candidates=candidates
    )

def get_heatmap_districts(complaint_id: str, db: Session) -> DistrictHeatmapResponse:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    predictions = (
        db.query(Prediction, WithdrawalLocation)
        .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
        .options(
            joinedload(WithdrawalLocation.district),
            noload(WithdrawalLocation.historical_cases),
            noload(WithdrawalLocation.predictions),
            noload(Prediction.factors),
        )
        .filter(Prediction.complaint_id == complaint_id)
        .all()
    )

    if not predictions:
        return DistrictHeatmapResponse(complaint_id=complaint_id, districts=[])

    district_map = {}
    
    for pred, loc in predictions:
        d = loc.district.district_name if loc.district else loc.district_id
        if d not in district_map:
            district_map[d] = {
                "count": 0,
                "max_prob": 0.0,
                "total_prob": 0.0,
                "min_rank": 999999
            }
            
        district_map[d]["count"] += 1
        prob = float(pred.risk_score)
        district_map[d]["total_prob"] += prob
        
        if prob > district_map[d]["max_prob"]:
            district_map[d]["max_prob"] = prob
            
        if pred.rank < district_map[d]["min_rank"]:
            district_map[d]["min_rank"] = pred.rank

    districts = []
    for d, stats in district_map.items():
        avg_prob = stats["total_prob"] / stats["count"]
        districts.append(DistrictAggregation(
            district_name=d,
            candidate_count=stats["count"],
            highest_probability=stats["max_prob"],
            average_probability=avg_prob,
            highest_rank=stats["min_rank"]
        ))
        
    # Sort by highest probability descending
    districts.sort(key=lambda x: x.highest_probability, reverse=True)

    return DistrictHeatmapResponse(
        complaint_id=complaint_id,
        districts=districts
    )

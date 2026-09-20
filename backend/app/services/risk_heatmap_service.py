from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.prediction import Prediction
from app.services.risk_service import get_risk_level
from app.models.withdrawal_location import WithdrawalLocation
from app.models.complaint import Complaint
from app.schemas.risk_heatmap import HeatmapCandidate, HeatmapResponse, DistrictAggregation, DistrictHeatmapResponse, GlobalHeatmapResponse, GlobalHeatmapCandidate

def get_global_heatmap(db: Session) -> GlobalHeatmapResponse:
    all_preds = (
        db.query(Prediction, WithdrawalLocation)
        .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
        .options(joinedload(WithdrawalLocation.district))
        .all()
    )
    if not all_preds:
        # Fallback to all withdrawal locations if no predictions exist yet
        locations = db.query(WithdrawalLocation).options(joinedload(WithdrawalLocation.district)).all()
        if not locations:
            raise HTTPException(status_code=404, detail="No candidate locations found")
        candidates = []
        for loc in locations:
            candidates.append(GlobalHeatmapCandidate(
                location_id=loc.location_id,
                latitude=loc.latitude,
                longitude=loc.longitude,
                district=loc.district.district_name if loc.district else loc.district_id,
                complaint_count=0,
                prediction_count=0,
                average_probability=0.0,
                maximum_probability=0.0,
                risk_level="LOW"
            ))
        return GlobalHeatmapResponse(candidates=candidates)

    # Aggregate by location_id
    agg_map = {}
    for pred, loc in all_preds:
        prob = float(pred.risk_score)
        loc_id = loc.location_id
        if loc_id not in agg_map:
            agg_map[loc_id] = {
                "loc": loc,
                "complaints": set(),
                "predictions": 0,
                "total_prob": 0.0,
                "max_prob": 0.0
            }
        
        agg_map[loc_id]["complaints"].add(pred.complaint_id)
        agg_map[loc_id]["predictions"] += 1
        agg_map[loc_id]["total_prob"] += prob
        if prob > agg_map[loc_id]["max_prob"]:
            agg_map[loc_id]["max_prob"] = prob

    candidates = []
    for loc_id, stats in agg_map.items():
        loc = stats["loc"]
        avg_prob = stats["total_prob"] / stats["predictions"] if stats["predictions"] > 0 else 0.0
        max_prob = stats["max_prob"]
        
        # Calculate risk level based on max_prob or avg_prob
        risk_level = get_risk_level(max_prob)

        candidates.append(GlobalHeatmapCandidate(
            location_id=loc_id,
            latitude=loc.latitude,
            longitude=loc.longitude,
            district=loc.district.district_name if loc.district else loc.district_id,
            complaint_count=len(stats["complaints"]),
            prediction_count=stats["predictions"],
            average_probability=avg_prob,
            maximum_probability=max_prob,
            risk_level=risk_level
        ))

    # Sort aggregated candidates by max probability descending
    candidates.sort(key=lambda x: (-x.maximum_probability, x.location_id))

    return GlobalHeatmapResponse(
        candidates=candidates
    )

def get_heatmap_candidates(complaint_id: str, db: Session, limit: int = 10) -> HeatmapResponse:
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    predictions = (
        db.query(Prediction, WithdrawalLocation)
        .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
        .options(joinedload(WithdrawalLocation.district))
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
        .options(joinedload(WithdrawalLocation.district))
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

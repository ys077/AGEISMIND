from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.prediction import Prediction
from app.models.withdrawal_location import WithdrawalLocation
from app.models.complaint import Complaint
from app.schemas.risk_heatmap import HeatmapCandidate, HeatmapResponse, DistrictAggregation, DistrictHeatmapResponse

def get_heatmap_candidates(complaint_id: str, db: Session) -> HeatmapResponse:
    if complaint_id == "ALL_COMPLAINTS":
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
                candidates.append(HeatmapCandidate(
                    prediction_id=f"GLOBAL_{loc.location_id}",
                    withdrawal_location_id=loc.location_id,
                    latitude=loc.latitude,
                    longitude=loc.longitude,
                    district=loc.district.district_name if loc.district else loc.district_id,
                    probability=0.0,
                    rank=999,
                    priority="LOW",
                    model_version="withdrawal_model_v1",
                    source=loc.source,
                    source_id=loc.source_id,
                    operator=loc.operator,
                    brand=loc.brand,
                    address=loc.address
                ))
            return HeatmapResponse(complaint_id=complaint_id, candidates=candidates)

        # Aggregate by location_id taking the prediction with maximum probability
        agg_map = {}
        for pred, loc in all_preds:
            prob = float(pred.risk_score)
            loc_id = loc.location_id
            if loc_id not in agg_map or prob > agg_map[loc_id]["prob"]:
                agg_map[loc_id] = {
                    "pred": pred,
                    "loc": loc,
                    "prob": prob
                }

        # Sort aggregated unique candidate locations by prob descending
        sorted_candidates = sorted(agg_map.values(), key=lambda x: (-x["prob"], x["loc"].location_id))

        candidates = []
        for rank, item in enumerate(sorted_candidates, start=1):
            pred = item["pred"]
            loc = item["loc"]
            candidates.append(HeatmapCandidate(
                prediction_id=str(pred.prediction_id),
                withdrawal_location_id=loc.location_id,
                latitude=loc.latitude,
                longitude=loc.longitude,
                district=loc.district.district_name if loc.district else loc.district_id,
                probability=item["prob"],
                rank=rank,
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
    else:
        complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        predictions = (
            db.query(Prediction, WithdrawalLocation)
            .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
            .options(joinedload(WithdrawalLocation.district))
            .filter(Prediction.complaint_id == complaint_id)
            .order_by(Prediction.rank.asc())
            .all()
        )

        if not predictions:
            raise HTTPException(status_code=404, detail="No predictions found for this complaint")

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
    if complaint_id == "ALL_COMPLAINTS":
        predictions = (
            db.query(Prediction, WithdrawalLocation)
            .join(WithdrawalLocation, Prediction.location_id == WithdrawalLocation.location_id)
            .options(joinedload(WithdrawalLocation.district))
            .all()
        )
    else:
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
        raise HTTPException(status_code=404, detail="No predictions found for this complaint")

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

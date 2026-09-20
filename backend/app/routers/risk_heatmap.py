from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.risk_heatmap import HeatmapResponse, DistrictHeatmapResponse, GlobalHeatmapResponse
from app.services import risk_heatmap_service

router = APIRouter()

@router.get(
    "/global",
    response_model=GlobalHeatmapResponse,
    summary="Get Global Risk Heatmap Candidates",
    description="Returns predicted withdrawal candidate locations aggregated across all complaints."
)
def get_global_heatmap_candidates(db: Session = Depends(get_db)):
    return risk_heatmap_service.get_global_heatmap(db)

@router.get(
    "/{complaint_id}",
    response_model=HeatmapResponse,
    summary="Get Risk Heatmap Candidates",
    description="Returns predicted withdrawal candidate locations for a specific complaint, formatted for map rendering."
)
def get_heatmap_candidates(
    complaint_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    return risk_heatmap_service.get_heatmap_candidates(complaint_id, db, limit)

@router.get(
    "/{complaint_id}/districts",
    response_model=DistrictHeatmapResponse,
    summary="Get Risk Heatmap District Aggregation",
    description="Returns district-level aggregated prediction statistics for a specific complaint."
)
def get_heatmap_districts(complaint_id: str, db: Session = Depends(get_db)):
    return risk_heatmap_service.get_heatmap_districts(complaint_id, db)

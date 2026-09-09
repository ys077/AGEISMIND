import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_time_geography_cc1001():
    response = client.get("/api/analysis/CC1001/time-geography")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_id"] == "CC1001"
    
    assert "temporal_analysis" in data
    assert "geographic_analysis" in data
    assert "withdrawal_candidate_features" in data
    assert "historical_comparison" in data
    assert "feature_vector" in data
    
    temp = data["temporal_analysis"]
    assert temp["transaction_count"] == 10
    assert temp["time_gaps"]["minimum_gap_minutes"] >= 0
    assert temp["time_gaps"]["maximum_gap_minutes"] >= 0
    assert temp["time_gaps"]["average_gap_minutes"] >= 0
    assert len(temp["period_activity"]) > 0
    
    geo = data["geographic_analysis"]
    assert geo["movement_summary"]["total_distance_km"] >= 0
    assert geo["movement_summary"]["district_transitions"] >= 0
    assert geo["movement_summary"]["unique_districts"] >= 1
    
    cand = data["withdrawal_candidate_features"]
    assert len(cand) > 0
    # Make sure no prediction scores exist
    assert "predicted_probability" not in cand[0]
    assert "final_rank" not in cand[0]
    
    vec = data["feature_vector"]
    assert "temporal_features" in vec
    assert "geographic_features" in vec

def test_get_time_analysis_cc1001():
    response = client.get("/api/analysis/CC1001/time")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_count"] == 10
    assert "time_gaps" in data
    assert "hourly_activity" in data
    assert "daily_activity" in data

def test_get_geography_analysis_cc1001():
    response = client.get("/api/analysis/CC1001/geography")
    assert response.status_code == 200
    data = response.json()
    assert "district_distribution" in data
    assert "movement_summary" in data

def test_get_withdrawal_candidates_features_cc1001():
    response = client.get("/api/analysis/CC1001/withdrawal-candidates/features")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_id"] == "CC1001"
    assert "candidates" in data
    assert len(data["candidates"]) > 0

def test_404_missing_complaint():
    assert client.get("/api/analysis/INVALID/time-geography").status_code == 404
    assert client.get("/api/analysis/INVALID/time").status_code == 404
    assert client.get("/api/analysis/INVALID/geography").status_code == 404
    assert client.get("/api/analysis/INVALID/withdrawal-candidates/features").status_code == 404

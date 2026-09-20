from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_heatmap_candidates_cc1001():
    # We must ensure prediction data exists. Module 8/9 tests typically run first, 
    # but we can explicitly trigger a prediction just in case.
    client.post("/api/predictions/CC1001")
    
    response = client.get("/api/risk-heatmap/CC1001")
    assert response.status_code == 200
    data = response.json()
    
    assert data["complaint_id"] == "CC1001"
    assert "candidates" in data
    
    candidates = data["candidates"]
    assert len(candidates) > 0
    
    # Check properties of the first candidate
    cand = candidates[0]
    assert "prediction_id" in cand
    assert "withdrawal_location_id" in cand
    assert "latitude" in cand
    assert "longitude" in cand
    assert "district" in cand
    assert "probability" in cand
    assert "rank" in cand
    assert "priority" in cand
    assert "model_version" in cand
    
    # Validate coordinate bounds (Tamil Nadu roughly)
    assert 8.0 <= cand["latitude"] <= 14.0
    assert 76.0 <= cand["longitude"] <= 81.0
    
    # Validate probability bounds
    assert 0.0 <= cand["probability"] <= 1.0

def test_get_heatmap_candidates_404():
    response = client.get("/api/risk-heatmap/MISSING_COMPLAINT")
    assert response.status_code == 404

def test_get_heatmap_districts_cc1001():
    client.post("/api/predictions/CC1001")
    
    response = client.get("/api/risk-heatmap/CC1001/districts")
    assert response.status_code == 200
    data = response.json()
    
    assert data["complaint_id"] == "CC1001"
    assert "districts" in data
    
    districts = data["districts"]
    assert len(districts) > 0
    
    # Check aggregation
    d = districts[0]
    assert "district_name" in d
    assert "candidate_count" in d
    assert "highest_probability" in d
    assert "average_probability" in d
    assert "highest_rank" in d
    
    assert d["candidate_count"] > 0
    assert 0.0 <= d["highest_probability"] <= 1.0
    assert 0.0 <= d["average_probability"] <= 1.0

def test_get_global_heatmap():
    client.post("/api/predictions/CC1001")
    
    response = client.get("/api/risk-heatmap/global")
    assert response.status_code == 200
    data = response.json()
    
    assert "candidates" in data
    assert len(data["candidates"]) > 0

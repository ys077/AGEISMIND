from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_explainability_global():
    res = client.get("/api/ml/explainability")
    assert res.status_code == 200
    data = res.json()
    assert "model_version" in data
    assert "global_feature_importance" in data
    assert "supported_model_type" in data
    assert "explanation_method" in data
    assert "SHAP" in data["explanation_method"]

def test_explainability_case_404():
    res = client.get("/api/explanations/NON_EXISTENT")
    assert res.status_code == 404

def test_explainability_case_cc1001():
    # Generate prediction first to ensure we have data
    client.post("/api/predictions/CC1001")
    
    res = client.get("/api/explanations/CC1001")
    assert res.status_code == 200
    data = res.json()
    assert data["complaint_id"] == "CC1001"
    assert "case_explanation" in data
    assert "overall_summary" in data["case_explanation"]
    assert "dominant_features" in data["case_explanation"]
    assert "candidates" in data
    
    candidates = data["candidates"]
    assert len(candidates) > 0
    
    # Check top candidate
    top_cand = candidates[0]
    assert "positive_factors" in top_cand
    assert "negative_factors" in top_cand
    
    pos_factors = top_cand["positive_factors"]
    neg_factors = top_cand["negative_factors"]
    assert len(pos_factors) + len(neg_factors) > 0
    
    if len(pos_factors) > 0:
        assert "explanation_text" in pos_factors[0]
        assert "feature_value" in pos_factors[0]
    elif len(neg_factors) > 0:
        assert "explanation_text" in neg_factors[0]
        assert "feature_value" in neg_factors[0]

def test_explainability_candidate_cc1001():
    # Fetch case to get top candidate ID
    res = client.get("/api/explanations/CC1001")
    top_location_id = res.json()["candidates"][0]["location_id"]
    
    res = client.get(f"/api/explanations/CC1001/candidates/{top_location_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["candidate"]["location_id"] == top_location_id
    assert "summary" in data["candidate"]
    
    # Check direction
    for f in data["candidate"]["positive_factors"]:
        assert f["direction"] == "POSITIVE"
        assert f["contribution"] > 0
        
    for f in data["candidate"]["negative_factors"]:
        assert f["direction"] == "NEGATIVE"
        assert f["contribution"] < 0

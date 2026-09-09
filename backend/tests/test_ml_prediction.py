import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_model_info():
    response = client.get("/api/ml/model-info")
    assert response.status_code == 200
    data = response.json()
    
    assert "model_type" in data
    assert "model_version" in data
    assert data["dataset_type"] == "SYNTHETIC_PROTOTYPE"
    assert "disclaimer" in data
    assert "evaluation" in data
    
    eval_metrics = data["evaluation"]
    assert "roc_auc" in eval_metrics
    assert "pr_auc" in eval_metrics
    assert "top_1_hit_rate" in eval_metrics
    assert "top_3_hit_rate" in eval_metrics
    assert "top_5_hit_rate" in eval_metrics
    assert "mrr" in eval_metrics
    assert eval_metrics["top_3_hit_rate"] is not None

def test_post_and_get_prediction_cc1001():
    # 1. Generate prediction via POST
    post_res = client.post("/api/predictions/CC1001")
    assert post_res.status_code == 200
    data = post_res.json()
    
    assert data["complaint_id"] == "CC1001"
    assert data["candidate_count"] == 25
    assert len(data["ranked_candidates"]) == 25
    
    candidates = data["ranked_candidates"]
    # Check ranks 1..25
    for idx, cand in enumerate(candidates):
        assert cand["rank"] == idx + 1
        assert 0.0 <= cand["probability"] <= 1.0
        assert cand["priority"] in ["HIGH", "MEDIUM", "LOW"]
        assert len(cand["location_id"]) > 0
        assert len(cand["district"]) > 0
        assert len(cand["location_name"]) > 0
        assert isinstance(cand["factors"], list)
        if len(cand["factors"]) > 0:
            f = cand["factors"][0]
            assert "factor_name" in f
            assert "contribution" in f
            assert f["direction"] in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
            
    # Probabilities should be monotonically non-increasing
    probs = [c["probability"] for c in candidates]
    assert all(probs[i] >= probs[i+1] for i in range(len(probs)-1))

    # 2. Retrieve prediction via GET
    get_res = client.get("/api/predictions/CC1001")
    assert get_res.status_code == 200
    stored_data = get_res.json()
    assert stored_data["complaint_id"] == "CC1001"
    assert len(stored_data["ranked_candidates"]) == 25

    # 3. Test top_k query parameter
    top5_res = client.get("/api/predictions/CC1001?top_k=5")
    assert top5_res.status_code == 200
    top5_data = top5_res.json()
    assert len(top5_data["ranked_candidates"]) == 5
    assert top5_data["ranked_candidates"][0]["rank"] == 1
    assert top5_data["ranked_candidates"][4]["rank"] == 5

def test_prediction_404_not_found():
    # POST with non-existent complaint
    res_post = client.post("/api/predictions/NON_EXISTENT_CASE")
    assert res_post.status_code == 404
    
    # GET with non-existent complaint
    res_get = client.get("/api/predictions/NON_EXISTENT_CASE")
    assert res_get.status_code == 404

def test_regression_existing_modules():
    # Test health
    assert client.get("/api/health").status_code == 200
    # Test complaints list
    assert client.get("/api/complaints").status_code == 200
    # Test specific complaint
    assert client.get("/api/complaints/CC1001").status_code == 200
    # Test analysis
    assert client.get("/api/analysis/CC1001").status_code == 200
    # Test money flow
    assert client.get("/api/analysis/CC1001/money-flow").status_code == 200
    # Test network analysis
    assert client.get("/api/analysis/CC1001/network").status_code == 200
    # Test time geography
    assert client.get("/api/analysis/CC1001/time-geography").status_code == 200

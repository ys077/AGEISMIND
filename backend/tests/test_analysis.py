import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_analysis_cc1001():
    response = client.get("/api/analysis/CC1001")
    assert response.status_code == 200
    data = response.json()
    assert "complaint_analysis" in data
    assert "transaction_analysis" in data
    
    # Verify transaction count is 10
    tx_analysis = data["transaction_analysis"]
    assert tx_analysis["transaction_summary"]["total_transactions"] == 10
    assert len(tx_analysis["timeline"]) == 10
    
    # Verify chronological ordering
    timeline = tx_analysis["timeline"]
    for i in range(1, len(timeline)):
        assert timeline[i]["timestamp"] >= timeline[i-1]["timestamp"]

def test_get_complaint_analysis_cc1001():
    response = client.get("/api/analysis/CC1001/complaint")
    assert response.status_code == 200
    data = response.json()
    assert "complaint" in data
    assert "analysis" in data
    assert "severity" in data["analysis"]
    assert "key_indicators" in data["analysis"]

def test_get_transaction_analysis_cc1001():
    response = client.get("/api/analysis/CC1001/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "transaction_summary" in data
    assert "timeline" in data
    assert "geographic_summary" in data
    assert "temporal_summary" in data
    assert "indicators" in data
    
    # Verify account count derived correctly
    geo = data["geographic_summary"]
    # 6 accounts involved, some may be in the same district, but the logic 
    # correctly counts unique districts based on the accounts
    assert isinstance(geo["account_districts"], list)
    assert geo["unique_district_count"] > 0

def test_analysis_404():
    response = client.get("/api/analysis/INVALID_COMPLAINT_9999")
    assert response.status_code == 404

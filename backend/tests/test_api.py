import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_complaints():
    response = client.get("/api/complaints?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) <= 5

def test_get_cc1001():
    response = client.get("/api/complaints/CC1001")
    assert response.status_code == 200
    data = response.json()
    assert data["complaint_id"] == "CC1001"

def test_get_cc1001_transactions():
    response = client.get("/api/complaints/CC1001/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

def test_get_cc1001_accounts():
    response = client.get("/api/complaints/CC1001/accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6

def test_get_cc1001_relationships():
    response = client.get("/api/complaints/CC1001/relationships")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 4

def test_get_cc1001_network():
    response = client.get("/api/complaints/CC1001/network")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 6
    assert len(data["edges"]) >= 4

def test_get_withdrawal_locations():
    response = client.get("/api/withdrawal-locations?page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

def test_get_historical_cases():
    response = client.get("/api/historical-cases?page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

def test_get_complete_case_cc1001():
    response = client.get("/api/cases/CC1001/complete")
    assert response.status_code == 200
    data = response.json()
    assert "complaint" in data
    assert data["complaint"]["complaint_id"] == "CC1001"
    assert "transactions" in data
    assert len(data["transactions"]) == 10
    assert "accounts" in data
    assert len(data["accounts"]) == 6
    assert "network" in data
    assert "candidate_withdrawal_locations" in data
    assert "historical_cases" in data

def test_404_missing_complaint():
    response = client.get("/api/complaints/MISSING123")
    assert response.status_code == 404

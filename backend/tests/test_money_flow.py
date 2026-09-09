import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_money_flow_cc1001():
    response = client.get("/api/analysis/CC1001/money-flow")
    assert response.status_code == 200
    data = response.json()
    assert "complaint_id" in data
    assert data["complaint_id"] == "CC1001"
    
    assert "source_accounts" in data
    assert "intermediary_accounts" in data
    assert "terminal_accounts" in data
    assert "paths" in data
    assert "account_flows" in data
    assert "flow_patterns" in data
    assert "flow_summary" in data
    
    # Validation against Module 5 rules for CC1001
    assert data["flow_summary"]["total_accounts"] == 6
    # 10 transactions processed successfully implies amount > 0 and path > 0
    assert data["flow_summary"]["total_paths"] > 0
    assert data["flow_summary"]["total_successful_amount"] > 0
    
def test_get_account_flow_cc1001():
    # First get the money flow to get an account_id
    response = client.get("/api/analysis/CC1001/money-flow")
    data = response.json()
    assert len(data["account_flows"]) > 0
    acc_id = data["account_flows"][0]["account_id"]
    
    # Now query the account flow
    acc_response = client.get(f"/api/analysis/CC1001/money-flow/accounts/{acc_id}")
    assert acc_response.status_code == 200
    acc_data = acc_response.json()
    assert acc_data["account_id"] == acc_id
    assert "role" in acc_data
    assert "incoming_transactions" in acc_data
    assert "outgoing_transactions" in acc_data
    assert "total_incoming" in acc_data
    assert "total_outgoing" in acc_data
    assert "time_gaps" in acc_data

def test_get_money_flow_404():
    response = client.get("/api/analysis/INVALID_123/money-flow")
    assert response.status_code == 404

def test_get_account_flow_404():
    response = client.get("/api/analysis/CC1001/money-flow/accounts/INVALID_ACC_123")
    assert response.status_code == 404

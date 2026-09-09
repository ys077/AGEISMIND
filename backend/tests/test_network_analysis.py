import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_network_analysis_cc1001():
    response = client.get("/api/analysis/CC1001/network-analysis")
    assert response.status_code == 200
    data = response.json()
    assert "complaint_id" in data
    assert data["complaint_id"] == "CC1001"
    
    assert "nodes" in data
    assert "edges" in data
    assert "network_summary" in data
    assert "centrality" in data
    assert "components" in data
    assert "district_distribution" in data
    assert "self_loops" in data
    assert "reciprocal_connections" in data
    assert "indicators" in data
    
    # Validation against Module 6 rules for CC1001
    assert len(data["nodes"]) == 6
    assert data["network_summary"]["total_accounts"] == 6
    assert data["network_summary"]["total_edges"] > 0
    assert data["network_summary"]["maximum_degree"] > 0
    
    # Check self loops for ACC100004 and ACC100006
    self_loop_accs = [sl["account_id"] for sl in data["self_loops"]]
    assert "ACC100004" in self_loop_accs
    assert "ACC100006" in self_loop_accs

def test_get_network_graph_cc1001():
    response = client.get("/api/analysis/CC1001/network-analysis/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 6
    assert len(data["edges"]) > 0

def test_get_account_network_cc1001():
    # First get the network to get an account_id
    response = client.get("/api/analysis/CC1001/network-analysis")
    data = response.json()
    assert len(data["nodes"]) > 0
    acc_id = data["nodes"][0]["account_id"]
    
    # Now query the account network
    acc_response = client.get(f"/api/analysis/CC1001/network-analysis/accounts/{acc_id}")
    assert acc_response.status_code == 200
    acc_data = acc_response.json()
    assert "account" in acc_data
    assert acc_data["account"]["account_id"] == acc_id
    assert "degree_metrics" in acc_data
    assert "centrality_metrics" in acc_data
    assert "incoming_connections" in acc_data
    assert "outgoing_connections" in acc_data
    assert "connected_accounts" in acc_data
    assert "component" in acc_data

def test_get_network_analysis_404():
    response = client.get("/api/analysis/INVALID_123/network-analysis")
    assert response.status_code == 404

def test_get_account_network_404():
    response = client.get("/api/analysis/CC1001/network-analysis/accounts/INVALID_ACC_123")
    assert response.status_code == 404

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_generate_alerts():
    """Test generating alerts from existing predictions."""
    response = client.post("/api/alerts/generate")
    assert response.status_code == 200
    data = response.json()
    assert "Generated" in data["message"]

def test_list_alerts():
    """Test listing alerts."""
    # Ensure alerts exist
    client.post("/api/alerts/generate")
    
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    
    if len(alerts) > 0:
        alert = alerts[0]
        assert "alert_id" in alert
        assert "prediction_id" in alert
        assert "probability" in alert
        assert "status" in alert

def test_get_alert_detail():
    """Test retrieving alert details with SHAP factors."""
    client.post("/api/alerts/generate")
    alerts = client.get("/api/alerts").json()
    
    if not alerts:
        pytest.skip("No alerts generated to test detail view.")
        
    alert_id = alerts[0]["alert_id"]
    response = client.get(f"/api/alerts/{alert_id}")
    
    assert response.status_code == 200
    detail = response.json()
    assert detail["alert_id"] == alert_id
    assert "top_positive_factors" in detail
    assert "top_negative_factors" in detail
    assert "explanation_text" in detail

def test_update_alert_status():
    """Test updating the status of an alert and verifying audit trail implicitly."""
    client.post("/api/alerts/generate")
    alerts = client.get("/api/alerts").json()
    
    if not alerts:
        pytest.skip("No alerts to test status update.")
        
    alert_id = alerts[0]["alert_id"]
    response = client.patch(f"/api/alerts/{alert_id}/status", json={"status": "IN_REVIEW"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_REVIEW"

def test_add_investigator_action():
    """Test adding an investigator action."""
    client.post("/api/alerts/generate")
    alerts = client.get("/api/alerts").json()
    
    if not alerts:
        pytest.skip("No alerts to test action.")
        
    alert_id = alerts[0]["alert_id"]
    response = client.post(f"/api/alerts/{alert_id}/actions", json={
        "action_type": "REVIEWED",
        "notes": "Test review action."
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Action recorded successfully"
    assert "action_id" in data

def test_get_alert_summary():
    """Test getting alert dashboard statistics."""
    client.post("/api/alerts/generate")
    response = client.get("/api/investigator/alerts/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "new_alerts" in data
    assert "high_priority" in data

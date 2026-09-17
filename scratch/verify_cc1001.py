import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("  END-TO-END SYSTEM VERIFICATION")
print("=" * 60)

# 1. Generate prediction for CC1001
post_res = client.post("/api/predictions/CC1001")
print(f"POST /api/predictions/CC1001 Status: {post_res.status_code}")
pred_data = post_res.json()
print(f"Candidate count: {pred_data['candidate_count']}")
print("Top 5 candidates:")
for c in pred_data["ranked_candidates"][:5]:
    print(f"  Rank {c['rank']}: ID={c['location_id']} Dist={c['district']} Prob={c['probability']:.4f} Priority={c['priority']}")

# 2. Risk Heatmap for CC1001
hm_res = client.get("/api/risk-heatmap/CC1001")
print(f"\nGET /api/risk-heatmap/CC1001 Status: {hm_res.status_code}")
hm_data = hm_res.json()
print(f"Heatmap candidate count: {len(hm_data['candidates'])}")
print("Top 3 Heatmap candidates:")
for c in hm_data["candidates"][:3]:
    print(f"  Rank {c['rank']}: ID={c['withdrawal_location_id']} ({c['latitude']}, {c['longitude']}) Prob={c['probability']:.4f}")

# 3. Risk Heatmap for ALL_COMPLAINTS
global_res = client.get("/api/risk-heatmap/ALL_COMPLAINTS")
print(f"\nGET /api/risk-heatmap/ALL_COMPLAINTS Status: {global_res.status_code}")
global_data = global_res.json()
print(f"Global Heatmap candidate count: {len(global_data['candidates'])}")

# 4. Generate Alerts
alert_gen_res = client.post("/api/alerts/generate")
print(f"\nPOST /api/alerts/generate: {alert_gen_res.json()}")

# 5. List Alerts
alerts_res = client.get("/api/alerts")
alerts = alerts_res.json()
print(f"Alerts returned: {len(alerts)}")

# 6. Audit Trail
audit_res = client.get("/api/audit")
audits = audit_res.json()
print(f"Audit records returned: {len(audits)}")

print("=" * 60)
print("  VERIFICATION COMPLETE")
print("=" * 60)

import logging
import sys

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("--- POST CC1001 ---", file=sys.stdout)
res = client.post("/api/predictions/CC1001")
print(res.status_code, file=sys.stdout)

print("--- GENERATE ALERTS ---", file=sys.stdout)
res = client.post("/api/alerts/generate")
print(res.status_code, file=sys.stdout)

print("--- GET ALERTS ---", file=sys.stdout)
res = client.get("/api/alerts")
print(res.status_code, file=sys.stdout)

print("--- POST CC1001 AGAIN ---", file=sys.stdout)
res = client.post("/api/predictions/CC1001")
print(res.status_code, file=sys.stdout)

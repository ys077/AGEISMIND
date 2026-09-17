import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.database import SessionLocal
from app.models import WithdrawalLocation, District
import math

session = SessionLocal()
wls = session.query(WithdrawalLocation).all()
dists = {d.district_id: d for d in session.query(District).all()}

print("Total WLs:", len(wls))
out_of_bounds = []
far_from_district = []

for wl in wls:
    lat = float(wl.latitude)
    lng = float(wl.longitude)
    d = dists.get(wl.district_id)
    
    # Check general TN bounding box
    if lat < 8.0 or lat > 13.6 or lng < 76.0 or lng > 80.4:
        out_of_bounds.append((wl.location_id, wl.district_id, lat, lng))
    
    # Check distance to district centroid (approx km)
    if d:
        d_lat = float(d.latitude)
        d_lng = float(d.longitude)
        dist_km = math.sqrt((lat - d_lat)**2 + (lng - d_lng)**2) * 111.0
        if dist_km > 100.0:  # More than 100 km away from claimed district centroid
            far_from_district.append((wl.location_id, wl.district_id, d.district_name, lat, lng, dist_km))

print(f"Points outside general TN bounding box (8.0-13.6N, 76.0-80.4E): {len(out_of_bounds)}")
if out_of_bounds:
    print("Sample out of bounds:", out_of_bounds[:5])

print(f"Points >100km from claimed district centroid: {len(far_from_district)}")
if far_from_district:
    print("Sample far from district:", far_from_district[:5])

session.close()

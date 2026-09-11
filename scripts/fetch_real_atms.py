import requests
import json
import csv
import math
import os

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_nearest_district(lat, lon, districts):
    nearest = None
    min_dist = float('inf')
    for d in districts:
        dist = haversine(lat, lon, float(d['latitude']), float(d['longitude']))
        if dist < min_dist:
            min_dist = dist
            nearest = d
    return nearest

def fetch_atms():
    print("Loading districts...")
    districts = []
    with open('data/raw/districts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        districts = list(reader)

    print("Fetching Tamil Nadu ATMs from Overpass API...")
    if os.path.exists('data/raw/osm_atms.json'):
        print("Using cached OSM data...")
        with open('data/raw/osm_atms.json', 'r', encoding='utf-8') as f:
            elements = json.load(f)
    else:
        query = """
        [out:json][timeout:60];
        area["name"="Tamil Nadu"]["admin_level"="4"]->.searchArea;
        (
          node["amenity"="atm"](area.searchArea);
          way["amenity"="atm"](area.searchArea);
        );
        out center;
        """
        url = "http://overpass-api.de/api/interpreter"
        headers = {"User-Agent": "AGEISMIND-Prototype/1.0"}
        response = requests.post(url, data={'data': query}, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        elements = data.get('elements', [])
        
        with open('data/raw/osm_atms.json', 'w', encoding='utf-8') as f:
            json.dump(elements, f, indent=2)
    print(f"Found {len(elements)} ATMs in Tamil Nadu.")

    # Deduplicate and validate
    unique_atms = {}
    for el in elements:
        lat = el.get('lat') or (el.get('center') and el.get('center').get('lat'))
        lon = el.get('lon') or (el.get('center') and el.get('center').get('lon'))
        
        if lat is None or lon is None:
            continue
            
        coord_key = f"{lat:.4f},{lon:.4f}"
        if coord_key in unique_atms:
            continue
            
        # Very rough TN bounds check just in case (already handled by Overpass Area though)
        if not (8.0 <= lat <= 14.0 and 76.0 <= lon <= 81.0):
            continue

        osm_id = str(el.get('id', ''))
        tags = el.get('tags', {})
        
        name = tags.get('name', 'ATM')
        operator = tags.get('operator', '')
        brand = tags.get('brand', '')
        
        # Address parts
        addr = []
        if 'addr:street' in tags: addr.append(tags['addr:street'])
        if 'addr:city' in tags: addr.append(tags['addr:city'])
        address = ", ".join(addr)

        unique_atms[coord_key] = {
            "source_id": osm_id,
            "latitude": lat,
            "longitude": lon,
            "name": name,
            "operator": operator,
            "brand": brand,
            "address": address
        }

    print(f"After deduplication: {len(unique_atms)} ATMs.")
    
    output_rows = []
    for idx, (coord, atm) in enumerate(unique_atms.items()):
        nearest_d = get_nearest_district(atm["latitude"], atm["longitude"], districts)
        
        output_rows.append({
            "location_id": f"OSM{idx+1:05d}",
            "district_id": nearest_d["district_id"],
            "location_reference_id": "",
            "location_name": atm["name"] if len(atm["name"]) < 200 else atm["name"][:197] + "...",
            "city": nearest_d["district_name"],
            "latitude": round(atm["latitude"], 4),
            "longitude": round(atm["longitude"], 4),
            "location_type": "ATM",
            "atm_count": 1,
            "area_risk_baseline": round(0.5, 2),
            "source": "OpenStreetMap",
            "source_id": atm["source_id"],
            "operator": atm["operator"][:100],
            "brand": atm["brand"][:100],
            "address": atm["address"][:255],
            "data_status": "real_world_reference"
        })

    # Save to CSV
    fields = list(output_rows[0].keys())
    with open('data/raw/withdrawal_locations.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)
        
    print("Saved real ATMs to data/raw/withdrawal_locations.csv")

if __name__ == "__main__":
    fetch_atms()
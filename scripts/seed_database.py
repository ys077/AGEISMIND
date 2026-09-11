"""
===============================================================================
DATABASE SEEDER — SYNTHETIC PROTOTYPE DATA (TAMIL NADU)
===============================================================================

Reads CSV files from data/raw/ and inserts them into PostgreSQL.
Resolves Foreign Keys and generates PostGIS Geography points natively.
"""

import csv
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(BASE_DIR, "backend"))

from app.core.config import settings
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")


def seed_districts(session: Session):
    path = os.path.join(RAW_DIR, "districts.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            geom = f"ST_SetSRID(ST_MakePoint({row['longitude']}, {row['latitude']}), 4326)"
            stmt = text(f"""
                INSERT INTO districts (district_id, district_name, state_name, latitude, longitude, geometry)
                VALUES (:id, :name, :state, :lat, :lon, {geom})
                ON CONFLICT (district_id) DO NOTHING
            """)
            session.execute(stmt, {
                "id": row["district_id"],
                "name": row["district_name"],
                "state": row["state_name"],
                "lat": row["latitude"],
                "lon": row["longitude"],
            })


def seed_locations(session: Session):
    path = os.path.join(RAW_DIR, "locations.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            geom = f"ST_SetSRID(ST_MakePoint({row['longitude']}, {row['latitude']}), 4326)"
            stmt = text(f"""
                INSERT INTO locations (location_id, district_id, location_name, city_or_town, location_type, latitude, longitude, geometry)
                VALUES (:id, :dist, :name, :city, :type, :lat, :lon, {geom})
                ON CONFLICT (location_id) DO NOTHING
            """)
            session.execute(stmt, {
                "id": row["location_id"],
                "dist": row["district_id"],
                "name": row["location_name"],
                "city": row["city_or_town"],
                "type": row["location_type"],
                "lat": row["latitude"],
                "lon": row["longitude"],
            })


def seed_accounts(session: Session):
    path = os.path.join(RAW_DIR, "accounts.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            geom = f"ST_SetSRID(ST_MakePoint({row['longitude']}, {row['latitude']}), 4326)"
            stmt = text(f"""
                INSERT INTO accounts (
                    account_id, district_id, account_type, city, 
                    latitude, longitude, account_risk_score, 
                    previous_case_count, account_status, location
                ) VALUES (
                    :aid, :dist, :atype, :city, :lat, :lon, :risk, :prev, :stat, {geom}
                ) ON CONFLICT (account_id) DO NOTHING
            """)
            session.execute(stmt, {
                "aid": row["account_id"],
                "dist": row["district_id"],
                "atype": row["account_type"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "risk": row["account_risk_score"],
                "prev": row["previous_case_count"],
                "stat": row["account_status"],
            })


def seed_complaints(session: Session):
    path = os.path.join(RAW_DIR, "complaints.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            geom = f"ST_SetSRID(ST_MakePoint({row['victim_longitude']}, {row['victim_latitude']}), 4326)"
            stmt = text(f"""
                INSERT INTO complaints (
                    complaint_id, district_id, complaint_date, complaint_time, fraud_type,
                    crime_category, fraud_amount, victim_city, victim_latitude,
                    victim_longitude, source_channel, status, location
                ) VALUES (
                    :cid, :dist, :cdate, :ctime, :ftype, :ccat, :famt, :vcity, :vlat, :vlon,
                    :src, :status, {geom}
                ) ON CONFLICT (complaint_id) DO NOTHING
            """)
            session.execute(stmt, {
                "cid": row["complaint_id"],
                "dist": row["district_id"],
                "cdate": row["complaint_date"],
                "ctime": row["complaint_time"],
                "ftype": row["fraud_type"],
                "ccat": row["crime_category"],
                "famt": row["fraud_amount"],
                "vcity": row["victim_city"],
                "vlat": row["victim_latitude"],
                "vlon": row["victim_longitude"],
                "src": row["source_channel"],
                "status": row["status"],
            })


def seed_transactions(session: Session):
    path = os.path.join(RAW_DIR, "transactions.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stmt = text("""
                INSERT INTO transactions (
                    transaction_id, complaint_id, sender_account, receiver_account,
                    amount, transaction_time, transaction_type, transaction_status
                ) VALUES (
                    :tid, :cid, :sndr, :rcvr, :amt, :ttime, :ttype, :tstat
                ) ON CONFLICT (transaction_id) DO NOTHING
            """)
            session.execute(stmt, {
                "tid": row["transaction_id"],
                "cid": row["complaint_id"],
                "sndr": row["sender_account"],
                "rcvr": row["receiver_account"],
                "amt": row["amount"],
                "ttime": row["transaction_time"],
                "ttype": row["transaction_type"],
                "tstat": row["transaction_status"],
            })


def seed_account_relationships(session: Session):
    path = os.path.join(RAW_DIR, "account_relationships.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stmt = text("""
                INSERT INTO account_relationships (
                    relationship_id, source_account, target_account,
                    relationship_type, total_amount, transaction_count
                ) VALUES (
                    :rid, :src, :tgt, :rtype, :amt, :cnt
                ) ON CONFLICT (relationship_id) DO NOTHING
            """)
            session.execute(stmt, {
                "rid": row["relationship_id"],
                "src": row["source_account"],
                "tgt": row["target_account"],
                "rtype": row["relationship_type"],
                "amt": row["total_amount"],
                "cnt": row["transaction_count"],
            })


def seed_withdrawal_locations(session: Session):
    path = os.path.join(RAW_DIR, "withdrawal_locations.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            geom = f"ST_SetSRID(ST_MakePoint({row['longitude']}, {row['latitude']}), 4326)"
            stmt = text(f"""
                INSERT INTO withdrawal_locations (
                    location_id, district_id, location_reference_id, location_name, city,
                    latitude, longitude, location_type, atm_count, area_risk_baseline, location,
                    source, source_id, operator, brand, address, data_status
                ) VALUES (
                    :lid, :dist, :lref, :lname, :city, :lat, :lon, :ltype, :atm, :risk, {geom},
                    :src, :sid, :op, :brnd, :addr, :dstat
                ) ON CONFLICT (location_id) DO NOTHING
            """)
            session.execute(stmt, {
                "lid": row["location_id"],
                "dist": row["district_id"],
                "lref": row["location_reference_id"] if row.get("location_reference_id") else None,
                "lname": row["location_name"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "ltype": row["location_type"],
                "atm": row["atm_count"],
                "risk": row["area_risk_baseline"],
                "src": row.get("source"),
                "sid": row.get("source_id"),
                "op": row.get("operator"),
                "brnd": row.get("brand"),
                "addr": row.get("address"),
                "dstat": row.get("data_status")
            })


def seed_historical_cases(session: Session):
    path = os.path.join(RAW_DIR, "historical_cases.csv")
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stmt = text("""
                INSERT INTO historical_cases (
                    historical_case_id, district_id, withdrawal_zone, fraud_type,
                    fraud_amount, transaction_hour, city, latitude, longitude,
                    account_risk, transaction_velocity, distance_to_location,
                    atm_density, historical_similarity, outcome
                ) VALUES (
                    :hcid, :dist, :wl_id, :ftype, :amt, :thour, :city, :lat, :lon,
                    :arisk, :tvel, :dist2, :atmd, :hsim, :out
                ) ON CONFLICT (historical_case_id) DO NOTHING
            """)
            session.execute(stmt, {
                "hcid": row["historical_case_id"],
                "dist": row["district_id"],
                "wl_id": row["withdrawal_location_id"],
                "ftype": row["fraud_type"],
                "amt": row["fraud_amount"],
                "thour": row["transaction_hour"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "arisk": row["account_risk"],
                "tvel": row["transaction_velocity"],
                "dist2": row["distance_to_location"],
                "atmd": row["atm_density"],
                "hsim": row["historical_similarity"],
                "out": row["outcome"],
            })


def main():
    print("=" * 60)
    print("  DATABASE SEEDER -- SYNTHETIC PROTOTYPE DATA (TAMIL NADU)")
    print("=" * 60)
    engine = create_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        try:
            print("Seeding districts...")
            seed_districts(session)
            print("Seeding locations...")
            seed_locations(session)
            print("Seeding accounts...")
            seed_accounts(session)
            print("Seeding complaints...")
            seed_complaints(session)
            print("Seeding transactions...")
            seed_transactions(session)
            print("Seeding account relationships...")
            seed_account_relationships(session)
            print("Seeding withdrawal locations...")
            seed_withdrawal_locations(session)
            print("Seeding historical cases...")
            seed_historical_cases(session)
            session.commit()
            print("All tables seeded successfully.")
        except Exception as e:
            session.rollback()
            print("ERROR during seeding:")
            print(str(e))
            raise e

if __name__ == "__main__":
    main()

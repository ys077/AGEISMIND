from sqlalchemy import create_engine, inspect, text
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ageismind")
engine = create_engine(DB_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()

with engine.connect() as conn:
    print("====================")
    print("DATABASE ROW COUNTS")
    print("====================")
    for table in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        print(f"Table '{table}': {count} rows")

    print("\n====================")
    print("PREDICTION COVERAGE")
    print("====================")
    res = conn.execute(text("SELECT COUNT(DISTINCT complaint_id) FROM predictions"))
    print(f"Complaints with predictions: {res.scalar()}")

    print("\n====================")
    print("ALERT COUNTS BY STATUS")
    print("====================")
    res = conn.execute(text("SELECT status, COUNT(*) FROM alerts GROUP BY status"))
    for row in res:
        print(f"{row[0]}: {row[1]}")

    print("\n====================")
    print("TRANSACTION TOTALS")
    print("====================")
    res = conn.execute(text("SELECT SUM(amount) FROM transactions"))
    print(f"Total transaction amount: {res.scalar()}")

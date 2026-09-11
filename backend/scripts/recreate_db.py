import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from app.db.database import engine
from app.models.base import Base

# Import all models to ensure they are registered with Base.metadata
from app.models.district import District
from app.models.location import Location
from app.models.account import Account
from app.models.complaint import Complaint
from app.models.transaction import Transaction
from app.models.account_relationship import AccountRelationship
from app.models.withdrawal_location import WithdrawalLocation
from app.models.historical_case import HistoricalCase
from app.models.prediction import Prediction

def recreate_db():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database recreated successfully.")

if __name__ == "__main__":
    recreate_db()

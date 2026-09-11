"""
Models package — imports all models so Alembic and SQLAlchemy can discover them.
"""

from app.models.base import Base
from app.models.district import District
from app.models.location import Location
from app.models.account import Account
from app.models.complaint import Complaint
from app.models.transaction import Transaction
from app.models.account_relationship import AccountRelationship
from app.models.withdrawal_location import WithdrawalLocation
from app.models.historical_case import HistoricalCase
from app.models.prediction import Prediction
from app.models.prediction_factor import PredictionFactor
from app.models.investigation_action import InvestigationAction
from app.models.audit_log import AuditLog
from app.models.alert import Alert

__all__ = [
    "Base",
    "District",
    "Location",
    "Account",
    "Complaint",
    "Transaction",
    "AccountRelationship",
    "WithdrawalLocation",
    "HistoricalCase",
    "Prediction",
    "PredictionFactor",
    "InvestigationAction",
    "AuditLog",
    "Alert",
]

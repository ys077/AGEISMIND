"""
SQLAlchemy model: historical_cases
"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HistoricalCase(Base):
    __tablename__ = "historical_cases"

    historical_case_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fraud_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    fraud_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
    )
    transaction_hour: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    account_risk: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False,
    )
    transaction_velocity: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    distance_to_location: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False,
    )
    atm_density: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    historical_similarity: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False,
    )
    withdrawal_zone: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("withdrawal_locations.location_id", ondelete="CASCADE"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    # --- ORM relationships ---
    district: Mapped["District"] = relationship(
        "District", back_populates="historical_cases",
    )
    withdrawal_location: Mapped["WithdrawalLocation"] = relationship(
        "WithdrawalLocation", back_populates="historical_cases",
    )

    def __repr__(self) -> str:
        return f"<HistoricalCase {self.historical_case_id} ({self.fraud_type})>"

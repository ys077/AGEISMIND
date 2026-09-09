"""
SQLAlchemy model: complaints
"""

import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import Date, Numeric, String, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    complaint_date: Mapped[datetime.date] = mapped_column(
        Date, nullable=False,
    )
    fraud_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    fraud_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
    )
    complaint_time: Mapped[datetime.time] = mapped_column(
        Time, nullable=False,
    )
    victim_city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    victim_latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    victim_longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    crime_category: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    source_channel: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    # PostGIS geographic point for victim location
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # --- ORM relationships ---
    district: Mapped["District"] = relationship(
        "District", back_populates="complaints",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="complaint", lazy="selectin",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="complaint", lazy="selectin",
    )
    investigation_actions: Mapped[list["InvestigationAction"]] = relationship(
        "InvestigationAction", back_populates="complaint", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Complaint {self.complaint_id} ({self.fraud_type})>"

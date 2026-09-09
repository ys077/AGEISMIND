"""
SQLAlchemy model: withdrawal_locations
"""

from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WithdrawalLocation(Base):
    __tablename__ = "withdrawal_locations"

    location_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_reference_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("locations.location_id", ondelete="SET NULL"),
        nullable=True,
    )
    location_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    location_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    atm_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    area_risk_baseline: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False,
    )

    # PostGIS geographic point
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # --- ORM relationships ---
    district: Mapped["District"] = relationship(
        "District", back_populates="withdrawal_locations",
    )
    location_reference: Mapped["Location"] = relationship(
        "Location", back_populates="withdrawal_locations",
    )
    historical_cases: Mapped[list["HistoricalCase"]] = relationship(
        "HistoricalCase", back_populates="withdrawal_location", lazy="selectin",
    )
    predictions: Mapped[list["Prediction"]] = relationship(
        "Prediction", back_populates="withdrawal_loc", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WithdrawalLocation {self.location_id} ({self.city})>"

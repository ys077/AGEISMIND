"""
SQLAlchemy model: districts
"""

import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class District(Base):
    __tablename__ = "districts"

    district_id: Mapped[str] = mapped_column(
        String(50), primary_key=True,
    )
    district_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
    )
    state_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Tamil Nadu",
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # PostGIS geographic point (representative center)
    geometry = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # --- ORM relationships ---
    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="district",
    )
    accounts: Mapped[list["Account"]] = relationship(
        "Account", back_populates="district",
    )
    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint", back_populates="district",
    )
    withdrawal_locations: Mapped[list["WithdrawalLocation"]] = relationship(
        "WithdrawalLocation", back_populates="district",
    )
    historical_cases: Mapped[list["HistoricalCase"]] = relationship(
        "HistoricalCase", back_populates="district",
    )

    def __repr__(self) -> str:
        return f"<District {self.district_id} ({self.district_name})>"

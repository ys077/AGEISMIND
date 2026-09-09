"""
SQLAlchemy model: locations
"""

from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Location(Base):
    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(
        String(50), primary_key=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    city_or_town: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    location_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 4), nullable=False,
    )

    # PostGIS geographic point
    geometry = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # --- ORM relationships ---
    district: Mapped["District"] = relationship(
        "District", back_populates="locations",
    )
    withdrawal_locations: Mapped[list["WithdrawalLocation"]] = relationship(
        "WithdrawalLocation", back_populates="location_reference",
    )

    def __repr__(self) -> str:
        return f"<Location {self.location_id} ({self.location_name})>"

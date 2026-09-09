"""
SQLAlchemy model: accounts
"""

from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("districts.district_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
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
    account_risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False,
    )
    previous_case_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    account_status: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    # PostGIS geographic point (SRID 4326 = WGS 84)
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # --- ORM relationships ---
    district: Mapped["District"] = relationship(
        "District", back_populates="accounts",
    )
    sent_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.sender_account",
        back_populates="sender",
        lazy="selectin",
    )
    received_transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        foreign_keys="Transaction.receiver_account",
        back_populates="receiver",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Account {self.account_id} ({self.city})>"

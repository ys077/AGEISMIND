"""
SQLAlchemy model: predictions

Stores ML model prediction outputs for complaint/location pairs.
Populated by future ML modules — left empty during seeding.
"""

import datetime
import uuid
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    complaint_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("withdrawal_locations.location_id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    rank: Mapped[int] = mapped_column(
        Integer, nullable=False,
    )
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- ORM relationships ---
    complaint: Mapped["Complaint"] = relationship(
        "Complaint", back_populates="predictions",
    )
    withdrawal_loc: Mapped["WithdrawalLocation"] = relationship(
        "WithdrawalLocation", back_populates="predictions",
    )
    factors: Mapped[list["PredictionFactor"]] = relationship(
        "PredictionFactor", back_populates="prediction", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Prediction {self.prediction_id} score={self.risk_score}>"

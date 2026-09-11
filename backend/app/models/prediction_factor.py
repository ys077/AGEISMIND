"""
SQLAlchemy model: prediction_factors

Stores per-prediction explainability information (feature contributions).
Populated by future ML modules — left empty during seeding.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PredictionFactor(Base):
    __tablename__ = "prediction_factors"

    factor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_name: Mapped[str] = mapped_column(
        String(100), nullable=False,
    )
    contribution: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    feature_value: Mapped[str] = mapped_column(
        String(255), nullable=True,
    )
    explanation_text: Mapped[str] = mapped_column(
        String(500), nullable=True,
    )

    # --- ORM relationships ---
    prediction: Mapped["Prediction"] = relationship(
        "Prediction", back_populates="factors",
    )

    def __repr__(self) -> str:
        return f"<PredictionFactor {self.factor_name} {self.contribution}>"

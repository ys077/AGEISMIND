"""
SQLAlchemy model: alerts

Stores investigator alerts generated from high-priority ML predictions.
"""

import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NEW"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- ORM relationships ---
    prediction: Mapped["Prediction"] = relationship(
        "Prediction", backref="alert"
    )

    def __repr__(self) -> str:
        return f"<Alert {self.alert_id} (Status: {self.status})>"

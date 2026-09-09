"""
SQLAlchemy model: investigation_actions

Stores investigator actions taken on complaints.
Populated by future investigation modules — left empty during seeding.
"""

import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InvestigationAction(Base):
    __tablename__ = "investigation_actions"

    action_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    complaint_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    investigator_id: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    action_description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # --- ORM relationships ---
    complaint: Mapped["Complaint"] = relationship(
        "Complaint", back_populates="investigation_actions",
    )

    def __repr__(self) -> str:
        return f"<InvestigationAction {self.action_id} ({self.action_type})>"

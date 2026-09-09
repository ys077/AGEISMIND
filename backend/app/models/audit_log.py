"""
SQLAlchemy model: audit_logs

Stores audit trail and data-integrity hashes for evidence integrity.
Populated by future modules — left empty during seeding.
"""

import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    complaint_id: Mapped[Optional[str]] = mapped_column(
        String(20),
        ForeignKey("complaints.complaint_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    data_hash: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True,
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.audit_id} ({self.action_type})>"

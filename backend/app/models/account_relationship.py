"""
SQLAlchemy model: account_relationships
"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AccountRelationship(Base):
    __tablename__ = "account_relationships"

    relationship_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    source_account: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_account: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    transaction_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
    )

    # --- ORM relationships ---
    source: Mapped["Account"] = relationship(
        "Account", foreign_keys=[source_account],
    )
    target: Mapped["Account"] = relationship(
        "Account", foreign_keys=[target_account],
    )

    def __repr__(self) -> str:
        return (
            f"<AccountRelationship {self.relationship_id} "
            f"{self.source_account} -> {self.target_account}>"
        )

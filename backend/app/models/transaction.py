"""
SQLAlchemy model: transactions
"""

import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(20), primary_key=True,
    )
    complaint_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("complaints.complaint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_account: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    receiver_account: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
    )
    transaction_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, index=True,
    )
    transaction_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )
    transaction_status: Mapped[str] = mapped_column(
        String(50), nullable=False,
    )

    # --- ORM relationships ---
    complaint: Mapped["Complaint"] = relationship(
        "Complaint", back_populates="transactions",
    )
    sender: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[sender_account],
        back_populates="sent_transactions",
    )
    receiver: Mapped["Account"] = relationship(
        "Account",
        foreign_keys=[receiver_account],
        back_populates="received_transactions",
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id} {self.amount}>"

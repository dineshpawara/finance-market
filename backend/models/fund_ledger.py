"""
Fund Ledger Model - SQLAlchemy 2.0 ORM Entity
==============================================
Double-entry bookkeeping and immutable financial audit ledger
tracking fund deposits, withdrawals, trade debits/credits, and balance history.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Numeric, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.trading_account import TradingAccount


class FundLedger(Base):
    """
    Fund ledger entity mapped to 'fund_ledger' table in PostgreSQL.
    """

    __tablename__ = "fund_ledger"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, default=None, index=True
    )
    description: Mapped[str] = mapped_column(Text, default="", server_default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    account: Mapped["TradingAccount"] = relationship("TradingAccount", back_populates="ledger_entries")

    def __repr__(self) -> str:
        return (
            f"<FundLedger(id={self.id}, account_id={self.account_id}, "
            f"type='{self.transaction_type}', amount={self.amount}, balance_after={self.balance_after})>"
        )

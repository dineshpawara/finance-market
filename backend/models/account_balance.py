"""
Account Balance Model - SQLAlchemy 2.0 ORM Entity
==================================================
Maintains virtual and real funds: available cash, margin holds,
and realized / unrealized profit and loss metrics.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.trading_account import TradingAccount


class AccountBalance(Base):
    """
    Account balance entity mapped to 'account_balances' table in PostgreSQL.
    """
    __tablename__ = "account_balances"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    available_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.0"),
        server_default="0.0",
        nullable=False
    )
    blocked_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.0"),
        server_default="0.0",
        nullable=False
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.0"),
        server_default="0.0",
        nullable=False
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.0"),
        server_default="0.0",
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    account: Mapped["TradingAccount"] = relationship(
        "TradingAccount",
        back_populates="balance"
    )

    @property
    def total_balance(self) -> Decimal:
        """Total funds committed plus available."""
        return self.available_balance + self.blocked_balance

    @property
    def total_equity(self) -> Decimal:
        """Net account liquidation value including unrealized P&L."""
        return self.available_balance + self.blocked_balance + self.unrealized_pnl

    def __repr__(self) -> str:
        return (
            f"<AccountBalance(id={self.id}, account_id={self.account_id}, "
            f"available={self.available_balance}, blocked={self.blocked_balance}, realized_pnl={self.realized_pnl})>"
        )

"""
Position Model - SQLAlchemy 2.0 ORM Entity
===========================================
Represents open and closed portfolio holdings, net position quantities,
average acquisition prices, and continuous mark-to-market P&L.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import BigInteger, Numeric, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.trading_account import TradingAccount
    from models.instrument import Instrument
    from models.position_event import PositionEvent


class Position(Base):
    """
    Position entity mapped to 'positions' table in PostgreSQL.
    """

    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0", nullable=False)
    average_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), default=Decimal("0.0"), server_default="0.0", nullable=False
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), default=Decimal("0.0"), server_default="0.0", nullable=False
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), default=Decimal("0.0"), server_default="0.0", nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("account_id", "instrument_id", name="uq_positions_account_instrument"),)

    # Relationships
    account: Mapped["TradingAccount"] = relationship("TradingAccount", back_populates="positions")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="positions")
    events: Mapped[List["PositionEvent"]] = relationship(
        "PositionEvent", back_populates="position", cascade="all, delete-orphan"
    )

    @property
    def is_open(self) -> bool:
        """Returns True if net holding is non-zero."""
        return self.quantity != 0

    @property
    def is_long(self) -> bool:
        """Returns True if position is net long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Returns True if position is net short."""
        return self.quantity < 0

    @property
    def total_pnl(self) -> Decimal:
        """Combined realized and unrealized profit / loss."""
        return self.realized_pnl + self.unrealized_pnl

    def __repr__(self) -> str:
        return (
            f"<Position(id={self.id}, account_id={self.account_id}, instrument_id={self.instrument_id}, "
            f"qty={self.quantity}, avg_price={self.average_price}, unrealized_pnl={self.unrealized_pnl})>"
        )

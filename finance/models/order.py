"""
Order Model - SQLAlchemy 2.0 ORM Entity
========================================
Represents market, limit, stop-loss orders placed by users across instruments,
tracking full lifecycle execution status, pricing, and fill quantities.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.trading_account import TradingAccount
    from models.instrument import Instrument
    from models.order_event import OrderEvent
    from models.execution import Execution


class Order(Base):
    """
    Order entity mapped to 'orders' table in PostgreSQL.
    """
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trading_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    order_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        default=None
    )
    trigger_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        default=None
    )
    product_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )
    validity: Mapped[str] = mapped_column(
        String(20),
        default="DAY",
        server_default="DAY",
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
        index=True
    )
    filled_quantity: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False
    )
    average_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        default=None
    )
    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
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
        back_populates="orders"
    )
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="orders"
    )
    events: Mapped[List["OrderEvent"]] = relationship(
        "OrderEvent",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    executions: Mapped[List["Execution"]] = relationship(
        "Execution",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    @property
    def is_filled(self) -> bool:
        """Returns True if order is completely filled."""
        return self.status == "COMPLETE" or (self.filled_quantity >= self.quantity and self.quantity > 0)

    @property
    def is_open(self) -> bool:
        """Returns True if order is actively open in the market."""
        return self.status in ("OPEN", "TRIGGER_PENDING")

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, side='{self.side}', order_type='{self.order_type}', "
            f"qty={self.quantity}, filled={self.filled_quantity}, status='{self.status}')>"
        )

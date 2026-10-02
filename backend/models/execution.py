"""
Execution Model - SQLAlchemy 2.0 ORM Entity
============================================
Represents individual trade fills and execution legs, capturing executed quantities,
fill prices, execution timestamps, and exchange/brokerage transaction charges.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import BigInteger, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.order import Order
    from models.instrument import Instrument
    from models.position_event import PositionEvent


class Execution(Base):
    """
    Execution entity mapped to 'executions' table in PostgreSQL.
    """

    __tablename__ = "executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    charges: Mapped[Decimal] = mapped_column(
        Numeric(20, 8), default=Decimal("0.0"), server_default="0.0", nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="executions")
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="executions")
    position_events: Mapped[List["PositionEvent"]] = relationship("PositionEvent", back_populates="execution")

    @property
    def trade_value(self) -> Decimal:
        """Computes gross turnover value for this execution fill."""
        return self.price * self.quantity

    def __repr__(self) -> str:
        return (
            f"<Execution(id={self.id}, order_id={self.order_id}, "
            f"qty={self.quantity}, price={self.price}, charges={self.charges})>"
        )

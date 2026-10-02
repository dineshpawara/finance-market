"""
Position Event Model - SQLAlchemy 2.0 ORM Entity
=================================================
Audit trail of position lifecycle changes: quantity adjustments,
price impact, and incremental realized P&L caused by trade execution fills.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Numeric,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.position import Position
    from models.execution import Execution


class PositionEvent(Base):
    """
    Position event entity mapped to 'position_events' table in PostgreSQL.
    """
    __tablename__ = "position_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quantity_change: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False
    )
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.0"),
        server_default="0.0",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    position: Mapped["Position"] = relationship(
        "Position",
        back_populates="events"
    )
    execution: Mapped["Execution"] = relationship(
        "Execution",
        back_populates="position_events"
    )

    def __repr__(self) -> str:
        return (
            f"<PositionEvent(id={self.id}, position_id={self.position_id}, execution_id={self.execution_id}, "
            f"qty_change={self.quantity_change}, price={self.price}, realized_pnl={self.realized_pnl})>"
        )

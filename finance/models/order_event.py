"""
Order Event Model - SQLAlchemy 2.0 ORM Entity
==============================================
Records immutable state transitions, broker events, and rejection reasons
for complete audit trail of order execution lifecycles.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.order import Order


class OrderEvent(Base):
    """
    Order event entity mapped to 'order_events' table in PostgreSQL.
    """
    __tablename__ = "order_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="events"
    )

    def __repr__(self) -> str:
        return (
            f"<OrderEvent(id={self.id}, order_id={self.order_id}, "
            f"event_type='{self.event_type}', status='{self.status}')>"
        )

"""
Market Tick Model - SQLAlchemy 2.0 ORM Entity
==============================================
Represents real-time tick-by-tick market data feeds, best bid/ask quotes,
and trade execution updates (TimescaleDB hypertable optimized).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.instrument import Instrument


class MarketTick(Base):
    """
    Market tick entity mapped to 'market_ticks' table in PostgreSQL / TimescaleDB.
    Primary Key: (instrument_id, time)
    """

    __tablename__ = "market_ticks"

    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    last_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    last_quantity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=None)
    bid_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True, default=None)
    bid_quantity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=None)
    ask_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8), nullable=True, default=None)
    ask_quantity: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=None)
    volume: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0", nullable=False)
    open_interest: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, default=None)
    source: Mapped[str] = mapped_column(String(50), default="FEED", server_default="FEED", nullable=False)

    __table_args__ = (PrimaryKeyConstraint("instrument_id", "time", name="pk_market_ticks"),)

    # Relationships
    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="ticks")

    def __repr__(self) -> str:
        return (
            f"<MarketTick(instrument_id={self.instrument_id}, time={self.time}, "
            f"last_price={self.last_price}, volume={self.volume})>"
        )

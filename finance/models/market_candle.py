"""
Market Candle Model - SQLAlchemy 2.0 ORM Entity
================================================
Represents OHLCV historical and real-time candle aggregations
across multiple timeframes (TimescaleDB hypertable optimized).
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
    PrimaryKeyConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.instrument import Instrument


class MarketCandle(Base):
    """
    Market candle entity mapped to 'market_candles' table in PostgreSQL / TimescaleDB.
    Primary Key: (instrument_id, timeframe, time)
    """
    __tablename__ = "market_candles"

    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True
    )
    timeframe: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        nullable=False
    )
    open: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False
    )
    high: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False
    )
    low: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False
    )
    close: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        nullable=False
    )
    volume: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        server_default="0",
        nullable=False
    )
    open_interest: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        default=None
    )

    __table_args__ = (
        PrimaryKeyConstraint("instrument_id", "timeframe", "time", name="pk_market_candles"),
    )

    # Relationships
    instrument: Mapped["Instrument"] = relationship(
        "Instrument",
        back_populates="candles"
    )

    def __repr__(self) -> str:
        return (
            f"<MarketCandle(instrument_id={self.instrument_id}, timeframe='{self.timeframe}', "
            f"time={self.time}, open={self.open}, high={self.high}, low={self.low}, close={self.close}, volume={self.volume})>"
        )

"""
Instrument Model - SQLAlchemy 2.0 ORM Entity
=============================================
Represents tradeable assets, contracts, equities, indices, and derivatives
with lot sizes, tick sizes, strike prices, and option types.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    SmallInteger,
    Integer,
    Numeric,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.exchange import Exchange
    from models.market_segment import MarketSegment
    from models.market_tick import MarketTick
    from models.market_candle import MarketCandle
    from models.order import Order
    from models.execution import Execution
    from models.position import Position


class Instrument(Base):
    """
    Instrument entity mapped to 'instruments' table in PostgreSQL.
    """
    __tablename__ = "instruments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    exchange_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("exchanges.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    segment_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("market_segments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    trading_symbol: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    instrument_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )
    isin: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default=None,
        index=True
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        default=None,
        index=True
    )
    strike_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 8),
        nullable=True,
        default=None
    )
    option_type: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default=None
    )
    lot_size: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False
    )
    tick_size: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0.05"),
        server_default="0.05",
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="instruments"
    )
    segment: Mapped["MarketSegment"] = relationship(
        "MarketSegment",
        back_populates="instruments"
    )
    ticks: Mapped[List["MarketTick"]] = relationship(
        "MarketTick",
        back_populates="instrument",
        cascade="all, delete-orphan"
    )
    candles: Mapped[List["MarketCandle"]] = relationship(
        "MarketCandle",
        back_populates="instrument",
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="instrument"
    )
    executions: Mapped[List["Execution"]] = relationship(
        "Execution",
        back_populates="instrument"
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position",
        back_populates="instrument"
    )

    def __repr__(self) -> str:
        return (
            f"<Instrument(id={self.id}, symbol='{self.symbol}', "
            f"trading_symbol='{self.trading_symbol}', instrument_type='{self.instrument_type}', "
            f"exchange_id={self.exchange_id}, segment_id={self.segment_id})>"
        )

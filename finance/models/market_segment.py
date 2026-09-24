"""
Market Segment Model - SQLAlchemy 2.0 ORM Entity
=================================================
Represents trading segments within an exchange (e.g. Equity, Futures & Options, Currency).
"""

from typing import List, TYPE_CHECKING
from sqlalchemy import SmallInteger, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.exchange import Exchange
    from models.instrument import Instrument


class MarketSegment(Base):
    """
    Market segment entity mapped to 'market_segments' table in PostgreSQL.
    """
    __tablename__ = "market_segments"

    id: Mapped[int] = mapped_column(
        SmallInteger,
        primary_key=True,
        autoincrement=True
    )
    exchange_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("exchanges.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False
    )

    # Relationships
    exchange: Mapped["Exchange"] = relationship(
        "Exchange",
        back_populates="segments"
    )
    instruments: Mapped[List["Instrument"]] = relationship(
        "Instrument",
        back_populates="segment"
    )

    def __repr__(self) -> str:
        return f"<MarketSegment(id={self.id}, exchange_id={self.exchange_id}, code='{self.code}', name='{self.name}')>"

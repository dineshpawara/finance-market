"""
Exchange Model - SQLAlchemy 2.0 ORM Entity
===========================================
Represents stock and derivatives exchanges (e.g. NSE, BSE, MCX)
with operational timezones and active status.
"""

from typing import List, TYPE_CHECKING
from sqlalchemy import SmallInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.market_segment import MarketSegment
    from models.instrument import Instrument


class Exchange(Base):
    """
    Exchange entity mapped to 'exchanges' table in PostgreSQL.
    """

    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kolkata",
        server_default="Asia/Kolkata",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    # Relationships
    segments: Mapped[List["MarketSegment"]] = relationship(
        "MarketSegment", back_populates="exchange", cascade="all, delete-orphan"
    )
    instruments: Mapped[List["Instrument"]] = relationship("Instrument", back_populates="exchange")

    def __repr__(self) -> str:
        return f"<Exchange(id={self.id}, code='{self.code}', name='{self.name}', is_active={self.is_active})>"

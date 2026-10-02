"""
Trading Account Model - SQLAlchemy 2.0 ORM Entity
==================================================
Represents user trading accounts with unique account numbers,
currency identifiers, and active/suspended operational status.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User
    from models.account_balance import AccountBalance
    from models.order import Order
    from models.position import Position
    from models.fund_ledger import FundLedger


class TradingAccount(Base):
    """
    Trading account entity mapped to 'trading_accounts' table in PostgreSQL.
    """
    __tablename__ = "trading_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        server_default="INR",
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        server_default="ACTIVE",
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="trading_accounts"
    )
    balance: Mapped[Optional["AccountBalance"]] = relationship(
        "AccountBalance",
        back_populates="account",
        uselist=False,
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    positions: Mapped[List["Position"]] = relationship(
        "Position",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    ledger_entries: Mapped[List["FundLedger"]] = relationship(
        "FundLedger",
        back_populates="account",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<TradingAccount(id={self.id}, user_id={self.user_id}, "
            f"account_number='{self.account_number}', currency='{self.currency}', status='{self.status}')>"
        )

"""
User Model - SQLAlchemy 2.0 ORM Entity
========================================
Represents registered user accounts in PostgreSQL for authentication,
paper trading wallets, and user session management.
"""

from datetime import datetime, timezone, timedelta
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import String, Boolean, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.master_key import MasterKey
    from models.user_session import UserSession
    from models.password_history import PasswordHistory
    from models.audit_log import AuditLog
    from models.trading_account import TradingAccount


class User(Base):
    """
    User entity mapped to 'users' table in PostgreSQL.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    password_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now() + interval '30 days'")
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

    # Relationships to child security & session entities
    master_keys: Mapped[List["MasterKey"]] = relationship(
        "MasterKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    password_history: Mapped[List["PasswordHistory"]] = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )
    trading_accounts: Mapped[List["TradingAccount"]] = relationship(
        "TradingAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, new_hash: str) -> None:
        """Sets a new password hash and updates change & expiration timestamps."""
        now = datetime.now(timezone.utc)
        self.password_hash = new_hash
        self.password_changed_at = now
        self.password_expires_at = now + timedelta(days=30)

    @property
    def is_password_expired(self) -> bool:
        """Checks if current timestamp is at or past password expiry."""
        return datetime.now(timezone.utc) >= self.password_expires_at

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}', is_active={self.is_active})>"

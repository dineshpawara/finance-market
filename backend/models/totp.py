"""
TOTP Model - SQLAlchemy 2.0 ORM Entity
=============================================
Verify code for 2FA authentication
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, ForeignKey, Integer, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User


class TOTP(Base):
    """
    TOTP entity mapped to 'totp' table in PostgreSQL.
    """

    __tablename__ = "totp"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    totp: Mapped[str] = mapped_column(String(255), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(255), nullable=False, default="PENDING")
    last_used_step: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    enabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="totp")

    def __repr__(self) -> str:
        return f"<TOTP(id={self.id}, user_id={self.user_id}, created_at={self.created_at})>"

"""
Master Key Model - SQLAlchemy 2.0 ORM Entity
=============================================
Stores single-use emergency recovery master keys or high-privilege authorization keys.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User


class MasterKey(Base):
    """
    Master key entity mapped to 'master_keys' table in PostgreSQL.
    """
    __tablename__ = "master_keys"

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
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="master_keys")

    @property
    def is_used(self) -> bool:
        """Returns True if this master key has already been consumed."""
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        """Returns True if the current time has passed expiration time."""
        return self.expires_at is not None and datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Returns True if the key is unused and unexpired."""
        return not self.is_used and not self.is_expired

    def mark_used(self) -> None:
        """Marks this key as used at the current UTC timestamp."""
        self.used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<MasterKey(id={self.id}, user_id={self.user_id}, "
            f"is_used={self.is_used}, is_expired={self.is_expired})>"
        )

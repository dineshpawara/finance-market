"""
User Session Model - SQLAlchemy 2.0 ORM Entity
==============================================
Manages active user authentication sessions, tokens, and revocation state.
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


class UserSession(Base):
    """
    User session entity mapped to 'user_sessions' table in PostgreSQL.
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    @property
    def is_revoked(self) -> bool:
        """Returns True if this session was explicitly invalidated."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Returns True if the current time has passed session expiration."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def is_active(self) -> bool:
        """Returns True if session is not revoked and not expired."""
        return not self.is_revoked and not self.is_expired

    def revoke(self) -> None:
        """Revokes this session immediately."""
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<UserSession(id={self.id}, user_id={self.user_id}, "
            f"is_active={self.is_active}, expires_at={self.expires_at})>"
        )

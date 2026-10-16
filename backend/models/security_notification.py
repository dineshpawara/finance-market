"""
Security Notification Model - SQLAlchemy 2.0 ORM Entity
=========================================================
Stores temporary in-app security notifications (e.g. newly rotated Master Keys).
Upon dismissal, sensitive payload content is permanently scrubbed.
"""

from datetime import datetime
from typing import Optional, Any, Dict, TYPE_CHECKING
import uuid

from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User


class SecurityNotification(Base):
    """
    In-app security notification entity mapped to 'security_notifications' table.
    """

    __tablename__ = "security_notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(50), default="NEW_MASTER_KEY", nullable=False)
    title: Mapped[str] = mapped_column(String(100), default="New Master Security Key", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    is_dismissed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", backref="security_notifications")

    def dismiss(self) -> None:
        """Dismisses notification and scrubs plaintext sensitive payload."""
        from datetime import timezone

        self.is_dismissed = True
        self.dismissed_at = datetime.now(timezone.utc)
        self.payload = None

    def __repr__(self) -> str:
        return f"<SecurityNotification(id={self.id}, user_id={self.user_id}, type='{self.type}', dismissed={self.is_dismissed})>"

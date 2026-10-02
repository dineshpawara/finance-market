"""
Audit Log Model - SQLAlchemy 2.0 ORM Entity
============================================
Logs user and system actions, entity modifications, and security events with JSONB metadata.
"""

from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
import uuid

from sqlalchemy import String, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from models.user import User


class AuditLog(Base):
    """
    Audit log entity mapped to 'audit_logs' table in PostgreSQL.
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    # 'metadata' is a reserved attribute on DeclarativeBase, so we map to column name "metadata" in DB
    metadata_: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    @property
    def payload(self) -> Dict[str, Any]:
        """Convenience property for accessing the JSONB metadata dictionary."""
        return self.metadata_ or {}

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action='{self.action}', entity_type='{self.entity_type}', entity_id={self.entity_id})>"
        )

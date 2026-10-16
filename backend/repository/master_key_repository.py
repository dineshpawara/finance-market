"""
Master Key Repository
=====================
Data Access Layer (Repository Pattern) for Master Keys, Password History,
User Sessions, and Security Audit Logs in PostgreSQL.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from models.user import User
from models.master_key import MasterKey
from models.password_history import PasswordHistory
from models.user_session import UserSession
from models.audit_log import AuditLog


class MasterKeyRepository:
    """
    Encapsulates all database operations and transactions for Master Key recovery,
    password modification, password history tracking, and security auditing.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_active_master_keys_by_user_id(self, user_id: uuid.UUID) -> List[MasterKey]:
        """
        Retrieves all active, unconsumed master security keys for a specific user.
        """
        stmt = (
            select(MasterKey)
            .where(
                MasterKey.user_id == user_id,
                MasterKey.used_at.is_(None),
            )
            .order_by(MasterKey.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Case-insensitive lookup of user by email address.
        """
        if not email:
            return None
        cleaned_email = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == cleaned_email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_user_by_id(self, user_id: uuid.UUID | str) -> Optional[User]:
        """
        Retrieves user by UUID primary key.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_recent_password_history(self, user_id: uuid.UUID, limit: int = 5) -> List[PasswordHistory]:
        """
        Retrieves historical password hashes for the user to prevent password reuse.
        """
        stmt = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def record_password_history(self, user_id: uuid.UUID, password_hash: str) -> PasswordHistory:
        """
        Archives an old password hash into the password_history table.
        """
        history_entry = PasswordHistory(
            id=uuid.uuid4(),
            user_id=user_id,
            password_hash=password_hash,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(history_entry)
        return history_entry

    def update_user_password(self, user: User, new_password_hash: str) -> None:
        """
        Updates the user's password hash and refreshes rotation timestamps.
        """
        now = datetime.now(timezone.utc)
        user.password_hash = new_password_hash
        user.password_changed_at = now
        user.password_expires_at = now + timedelta(days=30)
        self.db.add(user)

    def invalidate_user_sessions(self, user_id: uuid.UUID) -> int:
        """
        Terminates all active user sessions upon password reset.
        Returns the number of invalidated sessions.
        """
        stmt = delete(UserSession).where(UserSession.user_id == user_id)
        result = self.db.execute(stmt)
        return result.rowcount

    def record_audit_log(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        metadata: Dict[str, Any],
        entity_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        """
        Records a compliance/security event in the audit_logs table.
        """
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            entity_type="master_key",
            entity_id=entity_id or user_id,
            metadata_=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit_entry)
        return audit_entry

    def delete_user_master_keys(self, user_id: uuid.UUID) -> int:
        """
        Deletes existing master keys for a user upon rotation.
        """
        stmt = delete(MasterKey).where(MasterKey.user_id == user_id)
        result = self.db.execute(stmt)
        return result.rowcount

    def create_master_key(self, user_id: uuid.UUID, key_hash: str) -> MasterKey:
        """
        Persists a newly rotated master key hash in PostgreSQL.
        """
        record = MasterKey(
            id=uuid.uuid4(),
            user_id=user_id,
            key_hash=key_hash,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(record)
        return record

    def create_security_notification(
        self,
        user_id: uuid.UUID,
        notif_type: str,
        title: str,
        message: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Creates an unacknowledged in-app security notification.
        Cleans up any previous un-dismissed notifications of the same type.
        """
        from models.security_notification import SecurityNotification

        self.db.execute(
            delete(SecurityNotification).where(
                SecurityNotification.user_id == user_id,
                SecurityNotification.type == notif_type,
            )
        )

        notification = SecurityNotification(
            id=uuid.uuid4(),
            user_id=user_id,
            type=notif_type,
            title=title,
            message=message,
            payload=payload,
            is_dismissed=False,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(notification)
        return notification

    def get_active_notification(self, user_id: uuid.UUID, notif_type: str = "NEW_MASTER_KEY") -> Optional[Any]:
        """
        Retrieves the latest undismissed notification for the user.
        """
        from models.security_notification import SecurityNotification

        stmt = (
            select(SecurityNotification)
            .where(
                SecurityNotification.user_id == user_id,
                SecurityNotification.type == notif_type,
                SecurityNotification.is_dismissed.is_(False),
            )
            .order_by(SecurityNotification.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def dismiss_notification(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Any]:
        """
        Dismisses the notification and permanently scrubs any sensitive payload content.
        """
        from models.security_notification import SecurityNotification

        stmt = select(SecurityNotification).where(
            SecurityNotification.id == notification_id,
            SecurityNotification.user_id == user_id,
        )
        notification = self.db.scalars(stmt).first()
        if notification:
            notification.dismiss()
            self.db.add(notification)
        return notification

    def commit(self) -> None:
        """Commits the active transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rolls back the active transaction."""
        self.db.rollback()

"""
User Repository
===============
Data Access Layer (Repository Pattern) for User entities, active sessions,
and compliance audit logs in PostgreSQL.
"""

import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from models.user import User
from models.user_session import UserSession
from models.audit_log import AuditLog


class UserRepository:
    """
    Encapsulates all database operations and queries for users and authentication entities.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Case-insensitive lookup of user by email address.
        Trims whitespace and applies SQL lower() function for exact match.
        """
        if not email:
            return None
        cleaned_email = email.strip().lower()
        stmt = select(User).where(func.lower(User.email) == cleaned_email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: uuid.UUID | str) -> Optional[User]:
        """
        Retrieves user by primary key UUID.
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def record_user_session(
        self,
        user_id: uuid.UUID,
        access_token: str,
        expires_at: datetime,
    ) -> UserSession:
        """
        Records an active user session in PostgreSQL.
        Hashes the token with SHA-256 before storage so raw tokens are never persisted in plaintext.
        """
        token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
        session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(session)
        return session

    def record_audit_log(
        self,
        user_id: Optional[uuid.UUID],
        action: str,
        metadata: Dict[str, Any],
        entity_id: Optional[uuid.UUID] = None,
    ) -> AuditLog:
        """
        Records security and compliance events into the audit_logs table.
        """
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            entity_type="user",
            entity_id=entity_id or user_id,
            metadata_=metadata,
        )
        self.db.add(audit_entry)
        return audit_entry

    def commit(self) -> None:
        """Commits the active SQLAlchemy transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollbacks the active SQLAlchemy transaction upon exception."""
        self.db.rollback()

"""
TOTP Repository
===============
Data Access Layer (Repository Pattern) for TOTP entities in PostgreSQL.
Encapsulates all database operations, state transitions, failed attempt counters,
and account lockout management.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.totp import TOTP


class TOTPRepository:
    """
    Encapsulates all database queries and state updates for the TOTP 2FA entity.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[TOTP]:
        """
        Retrieves the TOTP record mapped to the specified user UUID.
        """
        stmt = select(TOTP).where(TOTP.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, totp_id: uuid.UUID) -> Optional[TOTP]:
        """
        Retrieves a TOTP record by its primary key UUID.
        """
        stmt = select(TOTP).where(TOTP.id == totp_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_or_update_pending(
        self,
        user_id: uuid.UUID,
        encrypted_secret: str,
        key_version: int = 1,
    ) -> TOTP:
        """
        Initializes or refreshes a PENDING 2FA registration for a user.
        If a record already exists, updates the encrypted secret and resets status to PENDING.
        """
        totp_record = self.get_by_user_id(user_id)
        if totp_record is None:
            totp_record = TOTP(
                id=uuid.uuid4(),
                user_id=user_id,
                totp=encrypted_secret,
                key_version=key_version,
                status="PENDING",
                last_used_step=0,
                failed_attempts=0,
                locked_until=None,
                enabled_at=None,
                last_used_at=None,
            )
            self.db.add(totp_record)
        else:
            totp_record.totp = encrypted_secret
            totp_record.key_version = key_version
            totp_record.status = "PENDING"
            totp_record.failed_attempts = 0
            totp_record.locked_until = None
            totp_record.enabled_at = None

        return totp_record

    def activate_totp(self, totp_record: TOTP, first_step: int) -> None:
        """
        Transitions TOTP state from PENDING to ACTIVE upon verifying the first passcode.
        Records step to prevent replay attacks and sets enabled_at timestamp.
        """
        now = datetime.now(timezone.utc)
        totp_record.status = "ACTIVE"
        totp_record.enabled_at = now
        totp_record.last_used_at = now
        totp_record.last_used_step = first_step
        totp_record.failed_attempts = 0
        totp_record.locked_until = None

    def record_failed_attempt(
        self,
        totp_record: TOTP,
        max_attempts: int = 5,
        lock_duration_minutes: int = 15,
    ) -> bool:
        """
        Increments failed passcode verification counter.
        Locks the account if failed attempts reach or exceed max_attempts.
        Returns True if the account is now locked.
        """
        totp_record.failed_attempts += 1
        if totp_record.failed_attempts >= max_attempts:
            totp_record.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_duration_minutes)
            return True
        return False

    def record_successful_verification(self, totp_record: TOTP, step: int) -> None:
        """
        Records successful OTP verification, updating last_used_step to prevent replay attacks
        and resetting failed attempts counter.
        """
        now = datetime.now(timezone.utc)
        totp_record.last_used_step = step
        totp_record.last_used_at = now
        totp_record.failed_attempts = 0
        totp_record.locked_until = None

    def disable_totp(self, totp_record: TOTP) -> None:
        """
        Sets status to DISABLED, deactivating 2FA enforcement.
        """
        totp_record.status = "DISABLED"
        totp_record.enabled_at = None

    def commit(self) -> None:
        """Commits active transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rolls back transaction on error."""
        self.db.rollback()

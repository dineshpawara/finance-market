"""
Master Key & Password Recovery Service
======================================
Enterprise business logic for Master Key verification, progressive brute-force lockout,
cryptographic two-stage ticket generation, and secure password updates.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

import jwt
from core.config import settings
from core.logging_config import app_logger, security_logger
from core.security import (
    DUMMY_HASH,
    hash_password,
    verify_password,
    _get_secret_key,
    JWT_ALGORITHM,
)
from database.redis_service import redis_service
from models.user import User
from repository.master_key_repository import MasterKeyRepository


class InvalidMasterKeyError(Exception):
    """Raised when the submitted Master Key does not match the stored hash."""

    pass


class MasterKeyLockoutError(Exception):
    """Raised when progressive brute-force threshold is breached."""

    pass


class InvalidResetTokenError(Exception):
    """Raised when the Stage-2 password reset token is invalid, expired, or replayed."""

    pass


class PasswordMismatchError(Exception):
    """Raised when new_password and confirm_password do not match."""

    pass


class PasswordReuseError(Exception):
    """Raised when user attempts to set a recently used password."""

    pass


# Security configuration
MAX_FAILED_ATTEMPTS: int = 5
LOCKOUT_DURATION_SECONDS: int = 900  # 15 minutes
RESET_TOKEN_VALIDITY_MINUTES: int = 15


class MasterKeyService:
    """
    Manages the lifecycle of Master Key recovery authorization.
    Enforces progressive brute-force rate-limiting, timing-attack mitigation,
    and single-use cryptographic tickets via Redis and PostgreSQL.
    """

    def __init__(self, repo: MasterKeyRepository):
        self.repo = repo
        self._memory_fails: Dict[str, int] = {}
        self._memory_lockout: Dict[str, datetime] = {}
        self._memory_tokens: Dict[str, str] = {}

    def _get_redis_client(self):
        """Returns the connected Redis client or None if offline."""
        return getattr(redis_service, "redis_client", None)

    def _check_lockout(self, client_ip: str) -> None:
        """Verifies if the client IP is currently in active brute-force lockout."""
        r = self._get_redis_client()
        lockout_key = f"master_key_lockout:{client_ip}"

        if r:
            try:
                ttl = r.ttl(lockout_key)
                if ttl > 0:
                    security_logger.warning(
                        f"[BRUTE-FORCE] Blocked request from locked-out IP '{client_ip}'. Remaining lockout: {ttl}s"
                    )
                    raise MasterKeyLockoutError(
                        f"Too many failed attempts. Access is locked for {ttl} seconds. Please try again later."
                    )
            except MasterKeyLockoutError:
                raise
            except Exception as e:
                app_logger.warning(f"[MasterKeyService] Redis lockout check error: {e}")
        else:
            # In-memory fallback check
            lock_until = self._memory_lockout.get(client_ip)
            if lock_until:
                now = datetime.now(timezone.utc)
                if now < lock_until:
                    remaining = int((lock_until - now).total_seconds())
                    raise MasterKeyLockoutError(f"Too many failed attempts. Access is locked for {remaining} seconds.")
                else:
                    del self._memory_lockout[client_ip]

    def _record_failure(self, client_ip: str, email: Optional[str] = None) -> int:
        """
        Increments failed attempt counter for client IP.
        Enforces 15-minute lockout when threshold of 5 attempts is reached.
        """
        r = self._get_redis_client()
        fails_key = f"master_key_fails:{client_ip}"
        lockout_key = f"master_key_lockout:{client_ip}"

        current_fails = 1
        if r:
            try:
                current_fails = r.incr(fails_key)
                if current_fails == 1:
                    r.expire(fails_key, LOCKOUT_DURATION_SECONDS)

                if current_fails >= MAX_FAILED_ATTEMPTS:
                    r.set(lockout_key, "1", ex=LOCKOUT_DURATION_SECONDS)
                    r.delete(fails_key)
                    security_logger.error(
                        f"[SECURITY ALERT] Master Key brute-force lockout triggered for IP '{client_ip}'. "
                        f"Target email: '{email or 'admin'}'. Locked for {LOCKOUT_DURATION_SECONDS}s."
                    )
            except Exception as e:
                app_logger.warning(f"[MasterKeyService] Redis failure tracking error: {e}")
        else:
            current_fails = self._memory_fails.get(client_ip, 0) + 1
            self._memory_fails[client_ip] = current_fails
            if current_fails >= MAX_FAILED_ATTEMPTS:
                self._memory_lockout[client_ip] = datetime.now(timezone.utc) + timedelta(
                    seconds=LOCKOUT_DURATION_SECONDS
                )
                self._memory_fails[client_ip] = 0

        return current_fails

    def _clear_failures(self, client_ip: str) -> None:
        """Resets failed attempt counters upon successful master key verification."""
        r = self._get_redis_client()
        if r:
            try:
                r.delete(f"master_key_fails:{client_ip}")
                r.delete(f"master_key_lockout:{client_ip}")
            except Exception as e:
                app_logger.warning(f"[MasterKeyService] Redis clear failure error: {e}")
        self._memory_fails.pop(client_ip, None)
        self._memory_lockout.pop(client_ip, None)

    def _create_reset_token(self, user: User) -> str:
        """
        Generates a 15-minute cryptographic JWT ticket for Stage 2 password reset.
        Enforces single-use via Redis unique jti token registration.
        """
        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_delta = timedelta(minutes=RESET_TOKEN_VALIDITY_MINUTES)
        expires_at = now + expires_delta

        claims = {
            "sub": str(user.id),
            "email": user.email,
            "purpose": "master_key_password_reset",
            "jti": jti,
            "iat": now,
            "nbf": now,
            "exp": expires_at,
        }

        secret_key = _get_secret_key()
        token = jwt.encode(claims, secret_key, algorithm=JWT_ALGORITHM)

        # Register token jti in Redis for single-use guarantee
        r = self._get_redis_client()
        token_key = f"reset_token:{jti}"
        if r:
            try:
                r.set(token_key, str(user.id), ex=LOCKOUT_DURATION_SECONDS)
            except Exception as e:
                app_logger.warning(f"[MasterKeyService] Failed to cache reset_token in Redis: {e}")
        else:
            self._memory_tokens[jti] = str(user.id)

        return token

    def verify_master_key(
        self,
        raw_key: str,
        email: Optional[str] = None,
        client_ip: str = "unknown",
        user_agent: Optional[str] = None,
    ) -> Tuple[str, User]:
        """
        Stage-1: Verifies raw master key against stored bcrypt hash in PostgreSQL.

        Security Safeguards:
        - Progressive brute-force lockout (5 strikes = 15m lock)
        - Constant-time verification against timing attacks
        - Cryptographic JWT ticket generation with single-use Redis registration
        - Regulatory audit logging
        """
        # Step 1: Check if IP is currently locked out
        self._check_lockout(client_ip)

        normalized_key = raw_key.strip().upper()

        # Step 2: Target User lookup (Explicit email or terminal single-admin default)
        target_email = email or getattr(settings, "seed_user_email", None)
        user = self.repo.get_user_by_email(target_email) if target_email else None

        # Step 3: Constant-time mitigation if user does not exist
        if user is None:
            verify_password(normalized_key, DUMMY_HASH)
            fails = self._record_failure(client_ip, email)
            remaining = max(0, MAX_FAILED_ATTEMPTS - fails)
            try:
                self.repo.record_audit_log(
                    user_id=None,
                    action="AUTH_MASTER_KEY_VERIFY_NONEXISTENT_USER",
                    metadata={
                        "submitted_email": target_email,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                    },
                )
                self.repo.commit()
            except Exception:
                self.repo.rollback()

            raise InvalidMasterKeyError(
                f"Invalid Master Security Key. {remaining} attempt(s) remaining before lockout."
            )

        # Step 4: Fetch active master security keys for this user
        active_keys = self.repo.get_active_master_keys_by_user_id(user.id)
        if not active_keys:
            verify_password(normalized_key, DUMMY_HASH)
            fails = self._record_failure(client_ip, user.email)
            remaining = max(0, MAX_FAILED_ATTEMPTS - fails)
            raise InvalidMasterKeyError(
                f"Invalid Master Security Key. {remaining} attempt(s) remaining before lockout."
            )

        # Step 5: Verify against active master keys
        is_match = False
        matching_key_id = None
        for key_obj in active_keys:
            if verify_password(normalized_key, key_obj.key_hash):
                is_match = True
                matching_key_id = key_obj.id
                break

        if not is_match:
            fails = self._record_failure(client_ip, user.email)
            remaining = max(0, MAX_FAILED_ATTEMPTS - fails)
            try:
                self.repo.record_audit_log(
                    user_id=user.id,
                    action="AUTH_MASTER_KEY_VERIFY_FAILED",
                    metadata={
                        "user_id": str(user.id),
                        "email": user.email,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "failed_attempt_number": fails,
                    },
                )
                self.repo.commit()
            except Exception:
                self.repo.rollback()

            if fails >= MAX_FAILED_ATTEMPTS:
                raise MasterKeyLockoutError(
                    "Too many failed attempts. Access is locked for 15 minutes. Please try again later."
                )

            raise InvalidMasterKeyError(
                f"Invalid Master Security Key. {remaining} attempt(s) remaining before lockout."
            )

        # Step 6: Success - Clear brute force counters & generate reset token
        self._clear_failures(client_ip)
        reset_token = self._create_reset_token(user)

        try:
            self.repo.record_audit_log(
                user_id=user.id,
                action="AUTH_MASTER_KEY_VERIFY_SUCCESS",
                metadata={
                    "user_id": str(user.id),
                    "email": user.email,
                    "master_key_id": str(matching_key_id),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                entity_id=matching_key_id,
            )
            self.repo.commit()
        except Exception as e:
            self.repo.rollback()
            app_logger.warning(f"[MasterKeyService] Error recording audit log: {e}")

        security_logger.info(
            f"[SECURITY] Master Key verified successfully for user '{user.email}' from IP '{client_ip}'. Reset token issued."
        )
        return reset_token, user

    def reset_password_with_token(
        self,
        reset_token: str,
        new_password: str,
        confirm_password: str,
        client_ip: str = "unknown",
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Stage-2: Sets a new password using the validated cryptographic reset token.

        Security Safeguards:
        - Signature, expiration, and purpose claim verification
        - Redis-backed single-use token consumption (anti-replay)
        - Password history check (prevents password reuse)
        - Bcrypt 12-round re-hashing
        - Active user sessions revocation in PostgreSQL
        - Audit compliance logging
        """
        if new_password != confirm_password:
            raise PasswordMismatchError("New password and confirm password do not match.")

        if len(new_password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        # Step 1: Decode and validate JWT reset token
        try:
            secret_key = _get_secret_key()
            payload = jwt.decode(reset_token, secret_key, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise InvalidResetTokenError("Reset token has expired. Please verify your Master Key again.")
        except jwt.InvalidTokenError:
            raise InvalidResetTokenError("Invalid reset token. Please verify your Master Key again.")

        if payload.get("purpose") != "master_key_password_reset":
            raise InvalidResetTokenError("Invalid token purpose. Expected password reset ticket.")

        user_id_str = payload.get("sub")
        jti = payload.get("jti")
        if not user_id_str or not jti:
            raise InvalidResetTokenError("Malformed reset token claims.")

        # Step 2: Verify Single-Use Token in Redis (Replay Attack Prevention)
        r = self._get_redis_client()
        token_key = f"reset_token:{jti}"
        if r:
            cached_user_id = r.get(token_key)
            if not cached_user_id or cached_user_id != user_id_str:
                raise InvalidResetTokenError(
                    "Reset token has already been consumed or is invalid. Please request a new verification."
                )
        else:
            cached_user_id = self._memory_tokens.get(jti)
            if not cached_user_id or cached_user_id != user_id_str:
                raise InvalidResetTokenError("Reset token has already been consumed or is invalid.")

        # Step 3: Fetch Target User
        user = self.repo.get_user_by_id(user_id_str)
        if not user or not user.is_active:
            raise InvalidResetTokenError("User account not found or is currently disabled.")

        # Step 4: Password Reuse Prevention
        if verify_password(new_password, user.password_hash):
            raise PasswordReuseError("New password cannot be the same as your current password.")

        recent_history = self.repo.get_recent_password_history(user.id, limit=5)
        for history_entry in recent_history:
            if verify_password(new_password, history_entry.password_hash):
                raise PasswordReuseError("New password cannot be the same as any of your recently used passwords.")

        # Step 5: Archive old password & Update with new bcrypt hash
        new_hash = hash_password(new_password)
        try:
            self.repo.record_password_history(user.id, user.password_hash)
            self.repo.update_user_password(user, new_hash)

            # Invalidate all active user sessions for session hijacking prevention
            invalidated_sessions = self.repo.invalidate_user_sessions(user.id)

            # Consume the reset token in Redis (Immediate invalidation)
            if r:
                r.delete(token_key)
            self._memory_tokens.pop(jti, None)

            # Step 6: Master Key Rotation & In-App Notification Delivery
            # Retire/delete the consumed master key
            deleted_keys_count = self.repo.delete_user_master_keys(user.id)

            # Generate a fresh cryptographically secure random Master Key
            from services.seed_service import generate_master_key

            new_raw_key = generate_master_key()
            new_key_hash = hash_password(new_raw_key)

            # Save newly hashed key to PostgreSQL master_keys table
            new_mk_record = self.repo.create_master_key(user.id, new_key_hash)

            # Create unacknowledged in-app security notification for Bell icon display
            self.repo.create_security_notification(
                user_id=user.id,
                notif_type="NEW_MASTER_KEY",
                title="New Master Security Key",
                message="Your previous master key was retired following a password reset. Store this newly generated key in a secure location immediately.",
                payload={"master_key": new_raw_key},
            )

            # Record audit compliance logs
            self.repo.record_audit_log(
                user_id=user.id,
                action="AUTH_PASSWORD_RESET_SUCCESS",
                metadata={
                    "user_id": str(user.id),
                    "email": user.email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "invalidated_sessions_count": invalidated_sessions,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            self.repo.record_audit_log(
                user_id=user.id,
                action="MASTER_KEY_ROTATED_ON_PASSWORD_RESET",
                metadata={
                    "user_id": str(user.id),
                    "email": user.email,
                    "new_master_key_id": str(new_mk_record.id),
                    "retired_keys_count": deleted_keys_count,
                    "client_ip": client_ip,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                entity_id=new_mk_record.id,
            )

            self.repo.commit()

        except Exception as e:
            self.repo.rollback()
            app_logger.error(f"[MasterKeyService] Error committing password reset and key rotation: {e}", exc_info=True)
            raise

        security_logger.info(
            f"[SECURITY] Password reset & Master Key rotation successful for user '{user.email}' from IP '{client_ip}'. "
            f"Rotated key ID: {new_mk_record.id}. Notification queued for user."
        )
        return user

    def get_pending_key_notification(self, user: User) -> Optional[Dict[str, Any]]:
        """
        Retrieves undismissed master key notification containing the one-time plaintext key.
        """
        notif = self.repo.get_active_notification(user.id, notif_type="NEW_MASTER_KEY")
        if not notif or notif.is_dismissed:
            return None

        master_key_str = notif.payload.get("master_key") if notif.payload else None
        if not master_key_str:
            return None

        return {
            "notification_id": str(notif.id),
            "title": notif.title,
            "message": notif.message,
            "master_key": master_key_str,
            "created_at": notif.created_at.isoformat()
            if hasattr(notif.created_at, "isoformat")
            else str(notif.created_at),
        }

    def dismiss_key_notification(self, notification_id: uuid.UUID | str, user: User) -> bool:
        """
        Dismisses the security notification and permanently scrubs the plaintext key payload.
        """
        if isinstance(notification_id, str):
            try:
                notification_id = uuid.UUID(notification_id)
            except ValueError:
                return False

        notif = self.repo.dismiss_notification(notification_id, user.id)
        if not notif:
            return False

        self.repo.record_audit_log(
            user_id=user.id,
            action="MASTER_KEY_NOTIFICATION_DISMISSED",
            metadata={
                "user_id": str(user.id),
                "notification_id": str(notification_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            entity_id=notification_id,
        )
        self.repo.commit()

        security_logger.info(
            f"[SECURITY] Master Key notification '{notification_id}' dismissed by user '{user.email}'. Plaintext scrubbed."
        )
        return True

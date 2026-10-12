"""
Two-Factor Authentication (2FA / TOTP) Business Service
======================================================
Enterprise business logic for RFC 6238 TOTP lifecycle:
- Cryptographic Base32 secret generation and Fernet encryption at rest
- QR code provisioning generation (Base64 PNG data URI)
- Replay attack mitigation via time-step tracking
- Brute-force progressive lockouts and financial-grade audit logging
"""

import io
import uuid
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

import pyotp
import qrcode

from core.crypto import encrypt_totp_secret, decrypt_totp_secret
from core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from core.logging_config import app_logger, security_logger
from models.user import User
from repository.totp_repository import TOTPRepository
from repository.user_repository import UserRepository


class TwoFactorError(Exception):
    """Base exception for 2FA domain errors."""

    pass


class TwoFactorNotConfiguredError(TwoFactorError):
    """Raised when 2FA is required but not configured or active for user."""

    pass


class TwoFactorAlreadyActiveError(TwoFactorError):
    """Raised when setup is attempted while 2FA is already active."""

    pass


class TwoFactorLockedError(TwoFactorError):
    """Raised when user account 2FA is locked due to too many failed attempts."""

    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class InvalidTwoFactorCodeError(TwoFactorError):
    """Raised when submitted 6-digit TOTP code is incorrect."""

    pass


class ReplayAttackError(TwoFactorError):
    """Raised when submitted code is valid but has already been used in this time step."""

    pass


class InvalidPreAuthTokenError(TwoFactorError):
    """Raised when the Stage-1 2FA temporary token is invalid, expired, or malformed."""

    pass


# Lifetime for Stage-1 Pre-Auth temporary token (5 minutes)
PREAUTH_TOKEN_EXPIRE_MINUTES = 5


def create_2fa_temp_token(user_id: uuid.UUID, email: str) -> str:
    """
    Issues a short-lived, single-purpose JWT token for Stage-2 2FA verification.
    Scoped strictly to '2fa_challenge' with a 5-minute validity window.
    """
    expires_delta = timedelta(minutes=PREAUTH_TOKEN_EXPIRE_MINUTES)
    claims = {
        "sub": str(user_id),
        "email": email,
        "scope": "2fa_challenge",
    }
    return create_access_token(data=claims, expires_delta=expires_delta)


def decode_2fa_temp_token(token: str) -> str:
    """
    Validates and decodes a Stage-1 Pre-Auth temporary token.
    Guarantees token possesses '2fa_challenge' scope and returns the user UUID string.
    """
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise InvalidPreAuthTokenError("Pre-authentication session expired or invalid.") from exc

    if payload.get("scope") != "2fa_challenge":
        raise InvalidPreAuthTokenError("Invalid token scope. A 2FA challenge token is required.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise InvalidPreAuthTokenError("Invalid token payload: missing user identifier.")

    return user_id_str


class TOTPService:
    """
    Enterprise Two-Factor Authentication Service.
    Enforces RFC 6238 standard, symmetric encryption, replay defenses, and audit logging.
    """

    def __init__(self, totp_repo: TOTPRepository, user_repo: UserRepository):
        self.totp_repo = totp_repo
        self.user_repo = user_repo

    def generate_setup(self, user: User) -> Tuple[str, str, str]:
        """
        Initializes 2FA enrollment for a user:
        1. Generates cryptographically secure Base32 secret seed (160-bit).
        2. Encrypts seed at rest with Fernet symmetric key and stores as PENDING.
        3. Formulates standard otpauth:// provisioning URI.
        4. Generates Base64 PNG QR code data URI.
        5. Emits audit log entry.
        """
        # Step 1: Generate RFC 3548 Base32 secret
        raw_secret = pyotp.random_base32(length=32)

        # Step 2: Encrypt secret at rest
        encrypted_secret = encrypt_totp_secret(raw_secret)

        # Step 3: Persist record in PENDING state
        try:
            self.totp_repo.create_or_update_pending(
                user_id=user.id,
                encrypted_secret=encrypted_secret,
                key_version=1,
            )
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="2FA_SETUP_INITIATED",
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
            )
            self.totp_repo.commit()
        except Exception as exc:
            self.totp_repo.rollback()
            app_logger.error(
                f"[TOTPService] Failed persisting pending TOTP setup for user {user.id}: {exc}", exc_info=True
            )
            raise

        # Step 4: Construct OTP provisioning URI
        totp_engine = pyotp.TOTP(raw_secret)
        otpauth_url = totp_engine.provisioning_uri(
            name=user.email,
            issuer_name="FinanceMarket",
        )

        # Step 5: Generate QR Code Base64 PNG Data URI
        qr_img = qrcode.make(otpauth_url, box_size=8, border=2)
        buffer = io.BytesIO()
        qr_img.save(buffer, "PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_data_uri = f"data:image/png;base64,{qr_base64}"

        app_logger.info(f"[TOTPService] 2FA setup generated for user '{user.email}' (ID: {user.id})")
        return raw_secret, otpauth_url, qr_data_uri

    def verify_setup(self, user: User, code: str) -> None:
        """
        Validates the user's first 6-digit TOTP code to confirm and activate 2FA:
        - Decrypts stored secret.
        - Validates code against RFC 6238 with clock drift tolerance.
        - Updates status to ACTIVE, stamps enabled_at, and records initial step.
        """
        totp_record = self.totp_repo.get_by_user_id(user.id)
        if not totp_record or totp_record.status != "PENDING":
            raise TwoFactorNotConfiguredError("No pending 2FA setup found. Please initiate setup first.")

        # Decrypt secret
        raw_secret = decrypt_totp_secret(totp_record.totp)
        totp_engine = pyotp.TOTP(raw_secret)

        cleaned_code = (code or "").strip()
        now = datetime.now(timezone.utc)
        base_timecode = totp_engine.timecode(now)

        # Check code with +/- 1 step clock skew tolerance
        matched_step = None
        for offset in (0, -1, 1):
            if cleaned_code == str(totp_engine.at(now, offset)):
                matched_step = base_timecode + offset
                break

        if matched_step is None:
            security_logger.warning(f"[TOTPService] Invalid 2FA setup verification code for user '{user.email}'")
            raise InvalidTwoFactorCodeError("Invalid 6-digit passcode. Please verify your Google Authenticator app.")

        # Activate 2FA
        try:
            self.totp_repo.activate_totp(totp_record, first_step=matched_step)
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="2FA_ACTIVATED",
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
            )
            self.totp_repo.commit()
        except Exception as exc:
            self.totp_repo.rollback()
            app_logger.error(f"[TOTPService] Failed activating 2FA for user {user.id}: {exc}", exc_info=True)
            raise

        security_logger.info(f"[TOTPService] 2FA successfully activated for user '{user.email}' (ID: {user.id})")

    def verify_login_passcode(
        self,
        user_id: uuid.UUID,
        code: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """
        Validates 6-digit TOTP passcode for Stage-2 login challenge:
        1. Checks account lockout (locked_until).
        2. Validates code against decrypted seed.
        3. Enforces replay attack defense (RFC 6238 §5.2).
        4. Resets failed attempts counter and logs audit success.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise TwoFactorNotConfiguredError("User account not found or disabled.")

        totp_record = self.totp_repo.get_by_user_id(user.id)
        if not totp_record or totp_record.status != "ACTIVE":
            raise TwoFactorNotConfiguredError("Two-Factor Authentication is not active for this account.")

        # Check lockout
        now = datetime.now(timezone.utc)
        if totp_record.locked_until and now < totp_record.locked_until:
            remaining_secs = int((totp_record.locked_until - now).total_seconds())
            remaining_mins = max(1, (remaining_secs + 59) // 60)
            security_logger.warning(
                f"[TOTPService] Rejected login: user '{user.email}' is locked until {totp_record.locked_until.isoformat()}"
            )
            raise TwoFactorLockedError(
                f"Account is temporarily locked due to too many failed attempts. Please retry in {remaining_mins} minute(s).",
                retry_after_seconds=remaining_secs,
            )

        # Decrypt secret
        raw_secret = decrypt_totp_secret(totp_record.totp)
        totp_engine = pyotp.TOTP(raw_secret)

        cleaned_code = (code or "").strip()
        base_timecode = totp_engine.timecode(now)

        # Validate code within acceptable window [-1, 0, +1]
        matched_step = None
        for offset in (0, -1, 1):
            if cleaned_code == str(totp_engine.at(now, offset)):
                matched_step = base_timecode + offset
                break

        # Case A: Code does not match
        if matched_step is None:
            is_locked = self.totp_repo.record_failed_attempt(totp_record, max_attempts=5, lock_duration_minutes=15)
            try:
                self.user_repo.record_audit_log(
                    user_id=user.id,
                    action="2FA_LOGIN_FAILED",
                    metadata={
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "failed_attempts": totp_record.failed_attempts,
                        "is_locked": is_locked,
                        "timestamp": now.isoformat(),
                    },
                )
                self.totp_repo.commit()
            except Exception:
                self.totp_repo.rollback()

            security_logger.warning(
                f"[TOTPService] Invalid 2FA code for user '{user.email}' from IP {client_ip} "
                f"(Attempts: {totp_record.failed_attempts}/5)"
            )

            if is_locked:
                raise TwoFactorLockedError(
                    "Account locked due to 5 consecutive failed passcodes. Please try again after 15 minutes.",
                    retry_after_seconds=900,
                )
            raise InvalidTwoFactorCodeError("Invalid 6-digit Google Authenticator passcode.")

        # Case B: Replay Attack Defense (Code already used in this 30s step)
        if matched_step <= totp_record.last_used_step:
            security_logger.warning(
                f"[TOTPService] Replay attack detected for user '{user.email}' from IP {client_ip} "
                f"(Step {matched_step} <= last_used_step {totp_record.last_used_step})"
            )
            raise ReplayAttackError(
                "Passcode has already been consumed for this time cycle. Please wait for Google Authenticator to generate a new code."
            )

        # Case C: Verification Success
        try:
            self.totp_repo.record_successful_verification(totp_record, step=matched_step)
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="2FA_LOGIN_SUCCESS",
                metadata={
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "step": matched_step,
                    "timestamp": now.isoformat(),
                },
            )
            self.totp_repo.commit()
        except Exception as exc:
            self.totp_repo.rollback()
            app_logger.error(
                f"[TOTPService] Failed persisting successful 2FA step for user {user.id}: {exc}", exc_info=True
            )
            raise

        security_logger.info(f"[TOTPService] 2FA successfully verified for user '{user.email}'")
        return user

    def get_status(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Queries current Two-Factor Authentication state for the user.
        """
        totp_record = self.totp_repo.get_by_user_id(user_id)
        if not totp_record:
            return {"is_enabled": False, "status": "NOT_CONFIGURED", "enabled_at": None}

        is_enabled = totp_record.status == "ACTIVE"
        enabled_at_str = totp_record.enabled_at.isoformat() if totp_record.enabled_at else None
        return {
            "is_enabled": is_enabled,
            "status": totp_record.status,
            "enabled_at": enabled_at_str,
        }

    def disable(self, user: User, code: str, password: str) -> None:
        """
        Disables 2FA security. Requires dual-factor authorization:
        1. Correct account password.
        2. Valid current 6-digit TOTP code.
        """
        if not verify_password(password, user.password_hash):
            raise InvalidTwoFactorCodeError("Incorrect account password.")

        totp_record = self.totp_repo.get_by_user_id(user.id)
        if not totp_record or totp_record.status != "ACTIVE":
            raise TwoFactorNotConfiguredError("2FA is not currently active on this account.")

        raw_secret = decrypt_totp_secret(totp_record.totp)
        totp_engine = pyotp.TOTP(raw_secret)
        if not totp_engine.verify((code or "").strip(), valid_window=1):
            raise InvalidTwoFactorCodeError("Invalid 6-digit Google Authenticator passcode.")

        try:
            self.totp_repo.disable_totp(totp_record)
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="2FA_DISABLED",
                metadata={"timestamp": datetime.now(timezone.utc).isoformat()},
            )
            self.totp_repo.commit()
        except Exception as exc:
            self.totp_repo.rollback()
            app_logger.error(f"[TOTPService] Failed disabling 2FA for user {user.id}: {exc}", exc_info=True)
            raise

        security_logger.info(f"[TOTPService] 2FA disabled for user '{user.email}' (ID: {user.id})")

"""
Authentication Service
======================
Business logic service for user login, credentials validation,
brute-force/timing attack mitigation, session generation, and audit trail.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from core.security import (
    DUMMY_HASH,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from core.logging_config import app_logger, security_logger
from models.user import User
from repository.user_repository import UserRepository
from repository.totp_repository import TOTPRepository
from services.totp_service import create_2fa_temp_token


class InvalidCredentialsError(Exception):
    """Raised when email not found or password does not match."""

    pass


class AccountDisabledError(Exception):
    """Raised when user account is inactive or disabled."""

    pass


class PasswordExpiredError(Exception):
    """Raised when password has passed its validity duration."""

    pass


class AuthService:
    """
    Enterprise Authentication Business Service.
    Enforces security policies, constant-time verification against timing attacks,
    auditing, and JWT token issuance.
    """

    def __init__(self, user_repo: UserRepository, totp_repo: Optional[TOTPRepository] = None):
        self.user_repo = user_repo
        self.totp_repo = totp_repo

    def login(
        self,
        email: str,
        password: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, User]:
        """
        Validates user credentials and issues a signed JWT access token.

        Security Safeguards:
        - Constant-Time verification to prevent timing attacks / user enumeration.
        - Case-insensitive, sanitized email comparison.
        - Account activity and password expiration checks.
        - Cryptographic session generation and financial-grade audit logging.
        """
        cleaned_email = (email or "").strip().lower()

        # Step 1: Look up user in database
        user = self.user_repo.get_by_email(cleaned_email)

        # Step 2: Constant-Time Dummy Verification (Prevents Timing Attacks)
        if user is None:
            verify_password(password, DUMMY_HASH)
            security_logger.warning(
                f"[AUTH] Failed login attempt: non-existent email '{cleaned_email}' from IP '{client_ip or 'unknown'}'"
            )
            raise InvalidCredentialsError("Invalid email or password")

        # Step 3: Verify Password Hash
        if not verify_password(password, user.password_hash):
            security_logger.warning(
                f"[AUTH] Failed login attempt: invalid password for user '{cleaned_email}' from IP '{client_ip or 'unknown'}'"
            )
            # Record failed login in audit logs
            try:
                self.user_repo.record_audit_log(
                    user_id=user.id,
                    action="AUTH_LOGIN_FAILED_INVALID_PASSWORD",
                    metadata={
                        "email": cleaned_email,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
                self.user_repo.commit()
            except Exception as e:
                self.user_repo.rollback()
                app_logger.warning(f"[AUTH] Could not write failed login audit log: {e}")

            raise InvalidCredentialsError("Invalid email or password")

        # Step 4: Validate Account Status
        if not user.is_active:
            security_logger.warning(
                f"[AUTH] Rejected login attempt: inactive account '{cleaned_email}' (User ID: {user.id})"
            )
            raise AccountDisabledError("Account is disabled. Please contact platform administrator.")

        # Step 5: Check Password Expiration Policy
        if user.is_password_expired:
            security_logger.warning(
                f"[AUTH] Rejected login attempt: expired password for user '{cleaned_email}' (User ID: {user.id})"
            )
            raise PasswordExpiredError("Password has expired. Please reset your password.")

        # Step 6: Multi-Factor Authentication (2FA) Check
        if self.totp_repo:
            totp = self.totp_repo.get_by_user_id(user.id)
            if totp and totp.status == "ACTIVE":
                temp_token = create_2fa_temp_token(user_id=user.id, email=user.email)
                security_logger.info(
                    f"[AUTH] Stage-1 credentials valid for user '{cleaned_email}'. 2FA challenge issued."
                )
                return temp_token, user, True

        # Step 7: Generate Signed JWT Bearer Token (Direct login when 2FA not active)
        token_expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.now(timezone.utc) + token_expires_delta

        token_claims = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
        }
        token = create_access_token(data=token_claims, expires_delta=token_expires_delta)

        # Step 8: Record User Session & Audit Log
        try:
            self.user_repo.record_user_session(
                user_id=user.id,
                access_token=token,
                expires_at=expires_at,
            )
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="AUTH_LOGIN_SUCCESS",
                metadata={
                    "email": cleaned_email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "auth_method": "PASSWORD_ONLY",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.user_repo.commit()
        except Exception as e:
            self.user_repo.rollback()
            app_logger.error(
                f"[AUTH] Error persisting login session or audit log for '{cleaned_email}': {e}",
                exc_info=True,
            )

        app_logger.info(f"[AUTH] User '{user.email}' logged in successfully.")
        return token, user, False

    def complete_2fa_login(
        self,
        user: User,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, User]:
        """
        Finalizes authentication after 2FA passcode has been verified.
        Issues 24-hour signed JWT access token, creates active UserSession, and logs audit record.
        """
        token_expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.now(timezone.utc) + token_expires_delta

        token_claims = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
        }
        token = create_access_token(data=token_claims, expires_delta=token_expires_delta)

        try:
            self.user_repo.record_user_session(
                user_id=user.id,
                access_token=token,
                expires_at=expires_at,
            )
            self.user_repo.record_audit_log(
                user_id=user.id,
                action="AUTH_LOGIN_SUCCESS",
                metadata={
                    "email": user.email,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "auth_method": "PASSWORD_AND_2FA",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.user_repo.commit()
        except Exception as e:
            self.user_repo.rollback()
            app_logger.error(
                f"[AUTH] Error persisting login session after 2FA for '{user.email}': {e}",
                exc_info=True,
            )

        app_logger.info(f"[AUTH] User '{user.email}' completed 2FA authentication successfully.")
        return token, user

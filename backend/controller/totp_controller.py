"""
Two-Factor Authentication (2FA) Controller
==========================================
HTTP Presentation layer controller managing request translation,
error mapping to application exceptions, and response serialization for 2FA.
"""

import uuid
from typing import Optional
from fastapi import Request

from core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    LockedException,
)
from core.logging_config import app_logger
from schemas.auth import LoginResponse, UserSummary
from schemas.two_factor import (
    TwoFactorSetupResponse,
    TwoFactorVerifySetupRequest,
    TwoFactorVerifySetupResponse,
    TwoFactorVerifyLoginRequest,
    TwoFactorStatusResponse,
    TwoFactorDisableRequest,
)
from services.totp_service import (
    TOTPService,
    TwoFactorLockedError,
    InvalidTwoFactorCodeError,
    ReplayAttackError,
    TwoFactorNotConfiguredError,
    TwoFactorAlreadyActiveError,
    InvalidPreAuthTokenError,
    decode_2fa_temp_token,
)
from services.auth_service import AuthService
from models.user import User


class TwoFactorController:
    """
    Coordinates 2FA HTTP presentation interactions.
    Binds HTTP requests to TOTPService and AuthService domain logic.
    """

    def __init__(self, totp_service: TOTPService, auth_service: AuthService):
        self.totp_service = totp_service
        self.auth_service = auth_service

    def setup(self, user: User) -> TwoFactorSetupResponse:
        """
        Generates a new TOTP secret seed, provisioning URI, and scannable QR code.
        """
        try:
            secret_key, otpauth_url, qr_code_base64 = self.totp_service.generate_setup(user)
            return TwoFactorSetupResponse(
                secret_key=secret_key,
                otpauth_url=otpauth_url,
                qr_code_base64=qr_code_base64,
                status="PENDING",
            )
        except TwoFactorAlreadyActiveError as err:
            raise BadRequestException(message=str(err))
        except Exception as err:
            app_logger.error(f"[TwoFactorController] Error during 2FA setup for user {user.id}: {err}", exc_info=True)
            raise BadRequestException(message="Could not initialize 2FA setup. Please try again.")

    def verify_setup(self, user: User, data: TwoFactorVerifySetupRequest) -> TwoFactorVerifySetupResponse:
        """
        Confirms the user's initial 6-digit TOTP passcode and transitions status to ACTIVE.
        """
        try:
            self.totp_service.verify_setup(user=user, code=data.code)
            return TwoFactorVerifySetupResponse(
                success=True,
                message="Google Authenticator 2FA activated successfully.",
                is_enabled=True,
            )
        except TwoFactorNotConfiguredError as err:
            raise BadRequestException(message=str(err))
        except InvalidTwoFactorCodeError as err:
            raise UnauthorizedException(message=str(err))
        except Exception as err:
            app_logger.error(f"[TwoFactorController] Error verifying setup for user {user.id}: {err}", exc_info=True)
            raise BadRequestException(message="Failed to verify setup code.")

    def verify_login_challenge(
        self,
        data: TwoFactorVerifyLoginRequest,
        request: Optional[Request] = None,
    ) -> LoginResponse:
        """
        Validates Stage-2 login 2FA passcode submitted with temporary pre-auth token.
        Issues final authenticated JWT Bearer access token upon success.
        """
        client_ip = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        # Step 1: Decode & validate Stage-1 pre-auth temporary token
        try:
            user_id_str = decode_2fa_temp_token(data.temp_token)
            user_uuid = uuid.UUID(user_id_str)
        except (InvalidPreAuthTokenError, ValueError) as err:
            app_logger.warning(f"[TwoFactorController] Invalid pre-auth token presented from IP {client_ip}")
            raise UnauthorizedException(
                message=str(err),
                details={"reason": "PREAUTH_TOKEN_INVALID"},
            )

        # Step 2: Validate 6-digit TOTP code against decrypted secret
        try:
            user = self.totp_service.verify_login_passcode(
                user_id=user_uuid,
                code=data.code,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except TwoFactorLockedError as err:
            app_logger.warning(f"[TwoFactorController] Locked user access attempt: user {user_uuid}")
            raise LockedException(
                message=str(err),
                details={"retry_after_seconds": err.retry_after_seconds},
            )
        except ReplayAttackError as err:
            app_logger.warning(f"[TwoFactorController] Replay attack attempt: user {user_uuid}")
            raise BadRequestException(
                message=str(err),
                details={"reason": "REPLAY_DETECTED"},
            )
        except InvalidTwoFactorCodeError as err:
            app_logger.warning(f"[TwoFactorController] Invalid 2FA code: user {user_uuid}")
            raise UnauthorizedException(
                message=str(err),
                details={"reason": "INVALID_TOTP_CODE"},
            )
        except TwoFactorNotConfiguredError as err:
            raise BadRequestException(message=str(err))

        # Step 3: Issue final 24-hour JWT Bearer token
        token, authenticated_user = self.auth_service.complete_2fa_login(
            user=user,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        return LoginResponse(
            requires_2fa=False,
            temp_token=None,
            access_token=token,
            token_type="bearer",
            expires_in=86400,
            user=UserSummary(
                id=str(authenticated_user.id),
                name=authenticated_user.name,
                email=authenticated_user.email,
                is_active=authenticated_user.is_active,
            ),
        )

    def get_status(self, user: User) -> TwoFactorStatusResponse:
        """
        Returns the current Two-Factor status for the authenticated user.
        """
        status_info = self.totp_service.get_status(user.id)
        return TwoFactorStatusResponse(
            is_enabled=status_info["is_enabled"],
            status=status_info["status"],
            enabled_at=status_info["enabled_at"],
        )

    def disable(self, user: User, data: TwoFactorDisableRequest) -> dict:
        """
        Deactivates 2FA upon verifying both current account password and current TOTP passcode.
        """
        try:
            self.totp_service.disable(user=user, code=data.code, password=data.password)
            return {"success": True, "message": "Two-Factor Authentication has been disabled."}
        except (InvalidTwoFactorCodeError, UnauthorizedException) as err:
            raise UnauthorizedException(message=str(err))
        except TwoFactorNotConfiguredError as err:
            raise BadRequestException(message=str(err))

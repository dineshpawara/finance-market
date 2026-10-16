"""
Master Key & Password Recovery Controller
=========================================
HTTP Presentation layer controller managing Master Key verification requests,
Stage-2 password updates, error mapping, and response serialization.
"""

from typing import Optional, Any
from fastapi import Request

from core.exceptions import (
    UnauthorizedException,
    BadRequestException,
    RateLimitException,
)
from core.logging_config import app_logger
from schemas.master_key import (
    MasterKeyVerifyRequest,
    MasterKeyVerifyResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    MasterKeyNotificationResponse,
    DismissNotificationRequest,
    DismissNotificationResponse,
)
from services.master_key_service import (
    MasterKeyService,
    InvalidMasterKeyError,
    MasterKeyLockoutError,
    InvalidResetTokenError,
    PasswordMismatchError,
    PasswordReuseError,
)


class MasterKeyController:
    """
    HTTP Controller coordinating the two-stage Master Key recovery flow.
    Acts as the boundary between FastAPI HTTP transport and the MasterKeyService.
    """

    def __init__(self, service: MasterKeyService):
        self.service = service

    def verify_master_key(
        self,
        data: MasterKeyVerifyRequest,
        request: Optional[Request] = None,
    ) -> MasterKeyVerifyResponse:
        """
        Stage-1: Coordinates Master Key verification and issues a 15-minute reset ticket.
        """
        client_ip = request.client.host if request and request.client else "unknown"
        user_agent = request.headers.get("user-agent") if request else None

        try:
            reset_token, user = self.service.verify_master_key(
                raw_key=data.master_key,
                email=data.email,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            return MasterKeyVerifyResponse(
                success=True,
                message="Master security key verified successfully. You may now reset your password.",
                reset_token=reset_token,
                expires_in=900,
            )

        except MasterKeyLockoutError as err:
            app_logger.warning(f"[MasterKeyController] Lockout enforced for IP '{client_ip}': {err}")
            raise RateLimitException(
                message=str(err),
                details={"client_ip": client_ip, "lockout": True},
            )

        except InvalidMasterKeyError as err:
            app_logger.warning(f"[MasterKeyController] Verification failed from IP '{client_ip}': {err}")
            raise UnauthorizedException(
                message=str(err),
                details={"client_ip": client_ip, "code": "INVALID_MASTER_KEY"},
            )

    def reset_password(
        self,
        data: PasswordResetRequest,
        request: Optional[Request] = None,
    ) -> PasswordResetResponse:
        """
        Stage-2: Sets a new password using the verified cryptographic ticket.
        """
        client_ip = request.client.host if request and request.client else "unknown"
        user_agent = request.headers.get("user-agent") if request else None

        try:
            self.service.reset_password_with_token(
                reset_token=data.reset_token,
                new_password=data.new_password,
                confirm_password=data.confirm_password,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            return PasswordResetResponse(
                success=True,
                message="Password reset successfully. Please log in with your new credentials.",
            )

        except PasswordMismatchError as err:
            raise BadRequestException(message=str(err), details={"code": "PASSWORD_MISMATCH"})

        except InvalidResetTokenError as err:
            raise UnauthorizedException(message=str(err), details={"code": "INVALID_RESET_TOKEN"})

        except PasswordReuseError as err:
            raise BadRequestException(message=str(err), details={"code": "PASSWORD_REUSE_FORBIDDEN"})

        except ValueError as err:
            raise BadRequestException(message=str(err), details={"code": "VALIDATION_ERROR"})

    def get_pending_notification(self, current_user: Any) -> MasterKeyNotificationResponse:
        """
        Retrieves active Master Key rotation notification for the authenticated user.
        """
        notif_data = self.service.get_pending_key_notification(current_user)
        if not notif_data:
            return MasterKeyNotificationResponse(has_notification=False)

        return MasterKeyNotificationResponse(
            has_notification=True,
            notification_id=notif_data["notification_id"],
            master_key=notif_data["master_key"],
            title=notif_data["title"],
            message=notif_data["message"],
            created_at=notif_data["created_at"],
        )

    def dismiss_notification(self, data: DismissNotificationRequest, current_user: Any) -> DismissNotificationResponse:
        """
        Dismisses the security notification and scrubs plaintext payload.
        """
        success = self.service.dismiss_key_notification(data.notification_id, current_user)
        if not success:
            raise BadRequestException(
                message="Notification not found or could not be dismissed.",
                details={"notification_id": data.notification_id},
            )

        return DismissNotificationResponse(
            success=True,
            message="Master key notification dismissed successfully.",
        )

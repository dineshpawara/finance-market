"""
Authentication Controller
=========================
HTTP Presentation layer controller managing request translation,
error mapping to application exceptions, and response serialization.
"""

from typing import Optional
from fastapi import Request

from core.config import settings
from core.exceptions import UnauthorizedException, ForbiddenException
from core.logging_config import app_logger
from schemas.auth import LoginRequest, LoginResponse, UserSummary
from services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    AccountDisabledError,
    PasswordExpiredError,
)


class AuthController:
    """
    Handles authentication HTTP interactions.
    Acts as the intermediary between HTTP transport (FastAPI Routes)
    and domain business logic (AuthService).
    """

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def login(self, data: LoginRequest, request: Optional[Request] = None) -> LoginResponse:
        """
        Coordinates user login, catches domain errors and maps them to HTTP AppExceptions.
        Single-admin terminal: If email is omitted in request, defaults to settings.seed_user_email from .env.
        """
        client_ip = request.client.host if request and request.client else None
        user_agent = request.headers.get("user-agent") if request else None

        # Resolve admin email: provided email or single-admin default from settings (.env)
        target_email = data.email or settings.seed_user_email
        if not target_email:
            raise UnauthorizedException("Admin user email is not configured in settings.")

        try:
            token, user, requires_2fa = self.auth_service.login(
                email=target_email,
                password=data.password,
                client_ip=client_ip,
                user_agent=user_agent,
            )

            if requires_2fa:
                return LoginResponse(
                    requires_2fa=True,
                    temp_token=token,
                    access_token=None,
                    token_type="bearer",
                    expires_in=300,
                    user=UserSummary(
                        id=str(user.id),
                        name=user.name,
                        email=user.email,
                        is_active=user.is_active,
                    ),
                )

            return LoginResponse(
                requires_2fa=False,
                temp_token=None,
                access_token=token,
                token_type="bearer",
                expires_in=86400,
                user=UserSummary(
                    id=str(user.id),
                    name=user.name,
                    email=user.email,
                    is_active=user.is_active,
                ),
            )

        except InvalidCredentialsError as err:
            app_logger.warning(f"[AuthController] Authentication failed for email: {data.email}")
            raise UnauthorizedException(
                message=str(err),
                details={"email": data.email},
            )

        except AccountDisabledError as err:
            app_logger.warning(f"[AuthController] Disabled account access attempted: {data.email}")
            raise ForbiddenException(
                message=str(err),
                details={"email": data.email},
            )

        except PasswordExpiredError as err:
            app_logger.warning(f"[AuthController] Expired password login attempted: {data.email}")
            raise ForbiddenException(
                message=str(err),
                details={"email": data.email},
            )

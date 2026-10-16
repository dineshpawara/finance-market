"""
Authentication API Routes (V1)
==============================
Provides endpoints for user authentication, token issuance, and session management.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from database.session import get_db
from repository.user_repository import UserRepository
from services.auth_service import AuthService
from controller.auth_controller import AuthController
from core.rate_limiter import limiter
from schemas.auth import LoginRequest, LoginResponse

from repository.totp_repository import TOTPRepository
from services.totp_service import TOTPService
from controller.totp_controller import TwoFactorController
from schemas.two_factor import TwoFactorVerifyLoginRequest

authRoute = APIRouter(prefix="/auth", tags=["Authentication V1"])


def get_auth_controller(db: Session = Depends(get_db)) -> AuthController:
    """Dependency factory assembling the repository -> service -> controller chain."""
    user_repo = UserRepository(db)
    totp_repo = TOTPRepository(db)
    service = AuthService(user_repo=user_repo, totp_repo=totp_repo)
    return AuthController(service)


def get_two_factor_controller(db: Session = Depends(get_db)) -> TwoFactorController:
    """Dependency factory assembling the 2FA repository -> service -> controller chain."""
    user_repo = UserRepository(db)
    totp_repo = TOTPRepository(db)
    auth_service = AuthService(user_repo=user_repo, totp_repo=totp_repo)
    totp_service = TOTPService(totp_repo=totp_repo, user_repo=user_repo)
    return TwoFactorController(totp_service=totp_service, auth_service=auth_service)


@authRoute.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT or 2FA challenge",
    description="Validates user credentials against PostgreSQL. If 2FA is active, issues temporary pre-auth challenge token; otherwise issues full JWT Bearer access token.",
)
@limiter.limit("5/minute")
def login_user(
    request: Request,
    response: Response,
    data: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> LoginResponse:
    """
    Clean Architecture flow:
    Route -> Controller -> Service -> Repository -> Database / Schemas
    """
    return controller.login(data=data, request=request)


@authRoute.post(
    "/2fa/verify",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Stage-2 Two-Factor Authentication Passcode",
    description="Validates 6-digit Google Authenticator passcode against temporary pre-auth token, issuing full JWT Bearer access token upon success.",
)
@limiter.limit("5/minute")
def verify_2fa_login(
    request: Request,
    response: Response,
    data: TwoFactorVerifyLoginRequest,
    controller: TwoFactorController = Depends(get_two_factor_controller),
) -> LoginResponse:
    """
    Stage-2 Login Challenge Flow:
    Client passes (temp_token + 6-digit code) -> Controller -> TOTPService & AuthService -> Database Session & JWT
    """
    return controller.verify_login_challenge(data=data, request=request)

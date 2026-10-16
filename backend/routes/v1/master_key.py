"""
Master Key & Password Recovery API Routes (V1)
==============================================
Provides endpoints for Master Security Key verification, progressive lockout,
and two-stage authenticated password resets.
"""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from database.session import get_db
from core.rate_limiter import limiter
from core.security import get_current_user
from models.user import User
from repository.master_key_repository import MasterKeyRepository
from services.master_key_service import MasterKeyService
from controller.master_key_controller import MasterKeyController
from schemas.master_key import (
    MasterKeyVerifyRequest,
    MasterKeyVerifyResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    MasterKeyNotificationResponse,
    DismissNotificationRequest,
    DismissNotificationResponse,
)

masterKeyRoute = APIRouter(prefix="/auth/master-key", tags=["Master Key & Password Recovery V1"])


def get_master_key_controller(db: Session = Depends(get_db)) -> MasterKeyController:
    """Dependency factory assembling the repository -> service -> controller chain."""
    repo = MasterKeyRepository(db)
    service = MasterKeyService(repo)
    return MasterKeyController(service)


@masterKeyRoute.post(
    "/verify",
    response_model=MasterKeyVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Master Security Key and Issue Reset Ticket",
    description=(
        "Stage-1 of Password Recovery. Validates raw Master Key against stored bcrypt hash. "
        "Enforces SlowAPI rate-limiting (5/min) and progressive 15-minute lockout upon 5 consecutive failed attempts. "
        "Returns a single-use 15-minute cryptographic JWT ticket upon success."
    ),
)
@limiter.limit("5/minute")
def verify_master_key(
    request: Request,
    response: Response,
    data: MasterKeyVerifyRequest,
    controller: MasterKeyController = Depends(get_master_key_controller),
) -> MasterKeyVerifyResponse:
    """
    Clean Architecture flow:
    Route -> Controller -> MasterKeyService (Redis lockout & Bcrypt verify) -> Schema
    """
    return controller.verify_master_key(data=data, request=request)


@masterKeyRoute.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Account Password Using Validated Ticket",
    description=(
        "Stage-2 of Password Recovery. Validates cryptographic reset token against Redis single-use registry. "
        "Prevents password reuse against historical hashes, hashes new password with bcrypt (12 rounds), "
        "terminates all active user sessions, and registers compliance audit logs."
    ),
)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    response: Response,
    data: PasswordResetRequest,
    controller: MasterKeyController = Depends(get_master_key_controller),
) -> PasswordResetResponse:
    """
    Clean Architecture flow:
    Route -> Controller -> MasterKeyService (Token verify & PostgreSQL update) -> Schema
    """
    return controller.reset_password(data=data, request=request)


@masterKeyRoute.get(
    "/notification",
    response_model=MasterKeyNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch Pending Rotated Master Key Notification",
    description=(
        "Retrieves any pending, unacknowledged Master Key rotation notification for the authenticated user. "
        "Used by the dashboard Bell Icon notification dropdown for one-time key retrieval."
    ),
)
def get_master_key_notification(
    current_user: User = Depends(get_current_user),
    controller: MasterKeyController = Depends(get_master_key_controller),
) -> MasterKeyNotificationResponse:
    """
    Clean Architecture flow:
    Route -> Controller -> MasterKeyService (Fetch un-dismissed key notification) -> Schema
    """
    return controller.get_pending_notification(current_user=current_user)


@masterKeyRoute.post(
    "/notification/dismiss",
    response_model=DismissNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Dismiss Master Key Notification and Scrub Plaintext",
    description=(
        "Marks the Master Key notification as dismissed and permanently scrubs the plaintext key payload "
        "from database storage, adhering to zero-knowledge storage principles."
    ),
)
def dismiss_master_key_notification(
    data: DismissNotificationRequest,
    current_user: User = Depends(get_current_user),
    controller: MasterKeyController = Depends(get_master_key_controller),
) -> DismissNotificationResponse:
    """
    Clean Architecture flow:
    Route -> Controller -> MasterKeyService (Dismiss & scrub payload in PostgreSQL) -> Schema
    """
    return controller.dismiss_notification(data=data, current_user=current_user)

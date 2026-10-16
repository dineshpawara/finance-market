"""
Master Key & Password Recovery Schemas
======================================
Pydantic v2 schemas for Master Security Key verification and Two-Stage Password Reset.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

MASTER_KEY_REGEX = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")


class MasterKeyVerifyRequest(BaseModel):
    """
    Stage-1 Request schema for validating the terminal Master Security Key.
    """

    master_key: str = Field(
        ...,
        min_length=16,
        max_length=25,
        description="Single-user Master Security Key in format XXXX-XXXX-XXXX-XXXX",
        examples=["WYI1-S9ZH-QT73-MF2F"],
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Optional registered email address (defaults to terminal single-admin)",
    )

    @field_validator("master_key")
    @classmethod
    def validate_master_key_format(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not MASTER_KEY_REGEX.match(cleaned):
            raise ValueError(
                "Invalid Master Key format. Expected 4 blocks of 4 alphanumeric characters (e.g. XXXX-XXXX-XXXX-XXXX)."
            )
        return cleaned


class MasterKeyVerifyResponse(BaseModel):
    """
    Stage-1 Response schema returning cryptographic reset ticket upon valid master key.
    """

    success: bool = Field(default=True, description="Master Key validation outcome")
    message: str = Field(..., description="Human-readable status notification")
    reset_token: str = Field(..., description="Time-limited signed cryptographic ticket for Step 2")
    expires_in: int = Field(default=900, description="Validity period of reset token in seconds (15 minutes)")


class PasswordResetRequest(BaseModel):
    """
    Stage-2 Request schema to set new password using the verified reset_token.
    """

    reset_token: str = Field(
        ...,
        min_length=20,
        description="Time-limited signed cryptographic reset token received from Stage 1",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="New secure password for the terminal account",
    )
    confirm_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Confirmation of the new password (must match new_password)",
    )

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New password and confirm password do not match.")
        return v


class PasswordResetResponse(BaseModel):
    """
    Stage-2 Response schema confirming successful credential update.
    """

    success: bool = Field(default=True, description="Password update outcome")
    message: str = Field(
        default="Password reset successfully. Please log in with your new credentials.",
        description="Status message",
    )


class MasterKeyNotificationResponse(BaseModel):
    """
    Response schema returning active un-dismissed security notification for Bell icon.
    """

    has_notification: bool = Field(..., description="Whether a pending master key notification exists")
    notification_id: Optional[str] = Field(default=None, description="Unique notification identifier")
    master_key: Optional[str] = Field(default=None, description="Plaintext new master key for one-time viewing")
    title: Optional[str] = Field(default=None, description="Notification title")
    message: Optional[str] = Field(default=None, description="Notification descriptive message")
    created_at: Optional[str] = Field(default=None, description="Notification creation timestamp")


class DismissNotificationRequest(BaseModel):
    """
    Request schema to dismiss the master key notification and scrub the plaintext key.
    """

    notification_id: str = Field(..., description="Notification ID to dismiss")


class DismissNotificationResponse(BaseModel):
    """
    Response schema confirming notification dismissal.
    """

    success: bool = Field(default=True, description="Dismissal outcome")
    message: str = Field(
        default="Master key notification dismissed successfully.",
        description="Status confirmation message",
    )

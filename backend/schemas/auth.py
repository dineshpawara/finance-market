from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class LoginRequest(BaseModel):
    """
    Schema for user authentication request payload.
    """

    email: Optional[EmailStr] = Field(
        default=None,
        description="Registered user email address (optional for single-user admin terminal)",
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Plaintext user password to verify against stored bcrypt hash",
    )


class UserSummary(BaseModel):
    """
    Lightweight user profile payload embedded in authentication response.
    """

    id: str = Field(..., description="Unique User UUID")
    name: str = Field(..., description="Full user display name")
    email: str = Field(..., description="Email address")
    is_active: bool = Field(..., description="Account active status")

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """
    Authentication response schema supporting both direct JWT token issuance
    and multi-stage 2FA challenges.
    """

    requires_2fa: bool = Field(default=False, description="True if Google Authenticator 2FA passcode is required")
    temp_token: Optional[str] = Field(default=None, description="Pre-auth session token to submit with 2FA passcode")
    access_token: Optional[str] = Field(default=None, description="Cryptographically signed JWT Bearer access token")
    token_type: Optional[str] = Field(default="bearer", description="Authentication token scheme")
    expires_in: Optional[int] = Field(default=86400, description="Token validity window in seconds (24 hours)")
    user: Optional[UserSummary] = Field(default=None, description="Authenticated user profile summary")

    model_config = ConfigDict(from_attributes=True)

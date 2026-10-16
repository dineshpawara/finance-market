"""
Services package initialization
"""

from .news_service import NewsService, news_service, RSS_FEEDS
from .auth_service import (
    AuthService,
    InvalidCredentialsError,
    AccountDisabledError,
    PasswordExpiredError,
)

from .seed_service import seed_default_user, seed_master_key_for_user
from .master_key_service import (
    MasterKeyService,
    InvalidMasterKeyError,
    MasterKeyLockoutError,
    InvalidResetTokenError,
    PasswordMismatchError,
    PasswordReuseError,
)

__all__ = [
    "NewsService",
    "news_service",
    "RSS_FEEDS",
    "AuthService",
    "InvalidCredentialsError",
    "AccountDisabledError",
    "PasswordExpiredError",
    "seed_default_user",
    "seed_master_key_for_user",
    "MasterKeyService",
    "InvalidMasterKeyError",
    "MasterKeyLockoutError",
    "InvalidResetTokenError",
    "PasswordMismatchError",
    "PasswordReuseError",
]

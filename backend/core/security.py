"""
Security & Cryptography Management
==================================
Handles password hashing, verification, JWT token generation & verification, and TOTP 2FA verification.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union
import bcrypt
import jwt

from core.config import settings


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against a hash."""
    if not password or not hashed:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# Precomputed 12-round bcrypt hash used for constant-time comparisons when a user is not found,
# preventing timing-based user enumeration attacks.
DUMMY_HASH: str = "$2b$12$e3RAw3mnSHMq730cuHpkYO5gfhOA5n/zIrJLOsTeE1L.kwdG17mEy"

# JWT Token Configuration
JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


def _get_secret_key() -> str:
    """
    Validates and retrieves SECRET_KEY from application settings.
    Strictly raises RuntimeError if SECRET_KEY is missing, empty, or an insecure placeholder.
    Zero fallback string allowed.
    """
    key = getattr(settings, "SECRET_KEY", None)
    if not key or not str(key).strip() or "insecure" in str(key).lower() or "change-this" in str(key).lower():
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: SECRET_KEY is not configured or is using an insecure default! "
            "A valid 256-bit secret key must be defined in .env before issuing or validating JWT tokens."
        )
    return str(key).strip()


def create_access_token(
    data: Union[Dict[str, Any], str],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a cryptographically signed JWT access token.
    Accepts either a string identifier (e.g. user_id) or a dictionary of custom claims.
    """
    to_encode: Dict[str, Any] = {}
    if isinstance(data, dict):
        to_encode = data.copy()
    else:
        to_encode = {"sub": str(data)}

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "iat": now,
            "nbf": now,
            "exp": expire,
        }
    )

    secret_key = _get_secret_key()
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a signed JWT token against the application secret key.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.
    """
    secret_key = _get_secret_key()
    return jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])


# HTTP Bearer Security Scheme for Header Authorization
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.session import get_db
from repository.user_repository import UserRepository
from core.exceptions import UnauthorizedException
import uuid

security_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency to extract and validate the authenticated user from the JWT Bearer token.
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication credentials were not provided. Please attach a Bearer token.")

    try:
        payload = decode_access_token(credentials.credentials)
    except Exception as exc:
        raise UnauthorizedException("Session expired or invalid token. Please log in again.") from exc

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Malformed token claims: missing user identifier.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed token subject UUID.")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_uuid)
    if not user or not user.is_active:
        raise UnauthorizedException("User account not found or inactive.")

    return user

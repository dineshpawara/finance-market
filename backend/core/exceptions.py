"""
Core Application Exceptions & Global Handlers
=============================================
Centralized, enterprise-grade exception handling for the Finance Market platform.
Provides standard domain exceptions with structured error codes and unified JSON responses.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Dedicated Loggers
app_logger = logging.getLogger("app.business")
error_logger = logging.getLogger("app.error")
security_logger = logging.getLogger("app.security")


class AppException(Exception):
    """
    Base application exception for handled/expected domain errors.
    All custom domain exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


# =====================================================================
# Specialized Domain Exceptions (Ready to use in Services & Routes)
# =====================================================================


class NotFoundException(AppException):
    """Resource not found (404)"""

    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND", details=details)


class BadRequestException(AppException):
    """Invalid input or failed business condition (400)"""

    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, error_code="BAD_REQUEST", details=details)


class UnauthorizedException(AppException):
    """Missing or invalid authentication token (401)"""

    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED", details=details)


class ForbiddenException(AppException):
    """Authenticated user lacks required permissions (403)"""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN", details=details)


class ConflictException(AppException):
    """Resource already exists or concurrent state conflict (409)"""

    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=409, error_code="CONFLICT", details=details)


class ValidationException(AppException):
    """Business logic validation failure (422)"""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR", details=details)


class RateLimitException(AppException):
    """API rate limit exceeded (429)"""

    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", details=details)


class ExternalServiceException(AppException):
    """Upstream API / External broker service failure (503)"""

    def __init__(self, message: str = "External service unavailable", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=503, error_code="EXTERNAL_SERVICE_UNAVAILABLE", details=details)


class InsufficientFundsException(AppException):
    """Trading account has insufficient balance to place order (400)"""

    def __init__(
        self, message: str = "Insufficient wallet funds for this order", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=400, error_code="INSUFFICIENT_FUNDS", details=details)


# =====================================================================
# Global Exception Handlers for FastAPI
# =====================================================================


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handles all AppException instances.
    Logs warnings for client errors (4xx) and errors for server-side domain errors (5xx).
    Logs security warnings for 401/403.
    """
    rid = getattr(request.state, "request_id", "-")
    client_ip = request.client.host if request.client else None

    log_payload = {
        "request_id": rid,
        "extra_data": {
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
            "client_ip": client_ip,
            "details": exc.details,
        },
    }

    # Route security vs business vs server errors
    if exc.status_code in (401, 403):
        security_logger.warning(f"Security rejection [{exc.error_code}]: {exc.message}", extra=log_payload)
    elif exc.status_code >= 500:
        error_logger.error(f"Application error [{exc.error_code}]: {exc.message}", extra=log_payload)
    else:
        app_logger.warning(f"Business rejection [{exc.error_code}]: {exc.message}", extra=log_payload)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details if exc.details else None,
            },
            "request_id": rid,
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Catches standard FastAPI / Starlette HTTPException (e.g. built-in 404, 405)
    and formats it in the same uniform JSON error structure.
    """
    rid = getattr(request.state, "request_id", "-")

    error_logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": rid,
            "extra_data": {
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
            },
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": None,
            },
            "request_id": rid,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unexpected crashes/bugs (500).
    Logs full exception with traceback for Loki/Grafana and returns a sanitized user-friendly message.
    """
    rid = getattr(request.state, "request_id", "-")

    error_logger.exception(
        f"Unhandled system crash: {str(exc)}",
        extra={
            "request_id": rid,
            "extra_data": {
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else None,
            },
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact support with the request ID.",
                "details": None,
            },
            "request_id": rid,
        },
    )

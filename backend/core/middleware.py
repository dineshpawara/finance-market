"""
HTTP Request Logging & Tracing Middleware
=========================================
Automatically records:
1. Access Logs: Method, Path, Status Code, Client IP, Latency (ms)
2. Performance Logs: Automatically flags requests exceeding SLA (e.g. > 500ms)
3. Security Logs: Automatically flags 401 Unauthorized / 403 Forbidden
4. Tracing: Generates or propagates X-Request-ID across the entire call stack
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response

from core.logging_config import (
    access_logger,
    perf_logger,
    security_logger,
    request_id_ctx,
    user_id_ctx,
)

# Latency threshold for performance warning (in milliseconds)
SLOW_REQUEST_THRESHOLD_MS = 500.0


def _log_request_completion(
    request: Request,
    request_id: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Helper to dispatch structured logs based on request completion status."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    user_id = user_id_ctx.get()

    extra_info = {
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params) if request.query_params else None,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "user_id": user_id,
    }

    # 1. Standard Access Log
    access_logger.info(
        f"{request.method} {request.url.path} -> {status_code} ({duration_ms}ms)",
        extra={"request_id": request_id, "extra_data": extra_info},
    )

    # 2. Performance SLA Warning (if request was slow)
    if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
        perf_logger.warning(
            f"Slow Request Detected: {request.method} {request.url.path} took {duration_ms}ms (threshold: {SLOW_REQUEST_THRESHOLD_MS}ms)",
            extra={"request_id": request_id, "extra_data": extra_info},
        )

    # 3. Security Warning (if rejected due to missing auth or permissions)
    if status_code in (401, 403):
        security_logger.warning(
            f"Security Rejection: {request.method} {request.url.path} returned HTTP {status_code} from {client_ip}",
            extra={"request_id": request_id, "extra_data": extra_info},
        )


async def log_requests(request: Request, call_next: Callable) -> Response:
    """FastAPI HTTP Middleware for automatic request logging and request ID correlation."""
    # Retrieve or generate request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id
    token_rid = request_id_ctx.set(request_id)

    # Extract user ID header if passed by API gateway/frontend
    user_id_header = request.headers.get("X-User-ID")
    token_uid = user_id_ctx.set(user_id_header if user_id_header else None)

    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        _log_request_completion(request, request_id, response.status_code, duration_ms)
    except Exception:
        # Request crashed: record 500 status in access log before propagating to unhandled_exception_handler
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        _log_request_completion(request, request_id, 500, duration_ms)
        raise
    finally:
        request_id_ctx.reset(token_rid)
        user_id_ctx.reset(token_uid)

    response.headers["X-Request-ID"] = request_id
    return response

"""
Core Logging Configuration
==========================
Comprehensive, production-ready logging system for Finance Market.
- Structured JSON output for Grafana Alloy / Loki ingestion
- Request ID & User ID propagation via ContextVars
- Automatic data sanitization (masks sensitive tokens & passwords)
- Categorized Rotating File Handlers (Access, App, Error, Audit, Security, Performance)
"""

import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional
from contextvars import ContextVar
from datetime import datetime, timezone

# Context variables for tracing across async tasks
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# Root directory of backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BACKEND_DIR / "logs"

# Sensitive keys to mask from log outputs
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "secret",
    "secret_key",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "pin",
    "otp",
    "cookie",
    "card_number",
    "cvv",
}


def sanitize_data(data: Any) -> Any:
    """Recursively mask sensitive values in dictionary or list payloads."""
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEYS):
                sanitized[k] = "******"
            elif isinstance(v, (dict, list)):
                sanitized[k] = sanitize_data(v)
            else:
                sanitized[k] = v
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


class RequestContextFilter(logging.Filter):
    """Injects request_id and user_id from async contextvars into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = request_id_ctx.get()
        if not hasattr(record, "user_id"):
            record.user_id = user_id_ctx.get()
        return True


class JsonLogFormatter(logging.Formatter):
    """
    Serializes each log entry into a single-line JSON string.
    Compliant with Loki / Promtail / Grafana Alloy structured ingestion.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Determine log category from logger name
        logger_name = record.name
        if "access" in logger_name:
            category = "access"
        elif "audit" in logger_name:
            category = "audit"
        elif "security" in logger_name:
            category = "security"
        elif "performance" in logger_name:
            category = "performance"
        elif "error" in logger_name or record.levelno >= logging.ERROR:
            category = "error"
        else:
            category = "application"

        iso_time = datetime.now(timezone.utc).isoformat()

        payload: Dict[str, Any] = {
            "timestamp": iso_time,
            "level": record.levelname,
            "category": category,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "caller": f"{record.module}.py:{record.lineno}",
        }

        user_id = getattr(record, "user_id", None)
        if user_id:
            payload["user_id"] = str(user_id)

        # Attach custom extra_data if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            payload["extra_data"] = sanitize_data(record.extra_data)

        # Include stack trace if exception info is present
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO", log_to_file: bool = True) -> None:
    """
    Initializes the logging infrastructure:
    - stdout StreamHandler (for Docker container logs & Alloy collection)
    - RotatingFileHandlers in backend/logs/ for file-based retention
    """
    os.makedirs(LOGS_DIR, exist_ok=True)

    json_formatter = JsonLogFormatter()
    context_filter = RequestContextFilter()

    # 1. Console / Stdout Handler (Always enabled for Docker & Alloy)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(json_formatter)
    stdout_handler.addFilter(context_filter)

    handlers = [stdout_handler]

    # 2. File Handlers with Rotation (10MB per file, 5 backups each)
    if log_to_file:
        max_bytes = 10 * 1024 * 1024  # 10 MB

        # Main application log
        app_file_handler = RotatingFileHandler(
            LOGS_DIR / "app.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        app_file_handler.setFormatter(json_formatter)
        app_file_handler.addFilter(context_filter)
        handlers.append(app_file_handler)

        # Error log (ERROR and CRITICAL only)
        error_file_handler = RotatingFileHandler(
            LOGS_DIR / "error.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(json_formatter)
        error_file_handler.addFilter(context_filter)
        handlers.append(error_file_handler)

        # Dedicated Access log handler
        access_file_handler = RotatingFileHandler(
            LOGS_DIR / "access.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        access_file_handler.setFormatter(json_formatter)
        access_file_handler.addFilter(context_filter)
        logging.getLogger("app.access").addHandler(access_file_handler)

        # Dedicated Audit log handler
        audit_file_handler = RotatingFileHandler(
            LOGS_DIR / "audit.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        audit_file_handler.setFormatter(json_formatter)
        audit_file_handler.addFilter(context_filter)
        logging.getLogger("app.audit").addHandler(audit_file_handler)

        # Dedicated Security log handler
        security_file_handler = RotatingFileHandler(
            LOGS_DIR / "security.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        security_file_handler.setFormatter(json_formatter)
        security_file_handler.addFilter(context_filter)
        logging.getLogger("app.security").addHandler(security_file_handler)

        # Dedicated Performance log handler
        perf_file_handler = RotatingFileHandler(
            LOGS_DIR / "performance.log", maxBytes=max_bytes, backupCount=5, encoding="utf-8"
        )
        perf_file_handler.setFormatter(json_formatter)
        perf_file_handler.addFilter(context_filter)
        logging.getLogger("app.performance").addHandler(perf_file_handler)

    # Configure Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers = handlers

    # Propagate Uvicorn & FastAPI logs through the same JSON pipeline
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(uvicorn_logger_name)
        lg.handlers = []
        lg.propagate = True


# =====================================================================
# Pre-configured Named Loggers for Application Components
# =====================================================================

app_logger = logging.getLogger("app.business")
access_logger = logging.getLogger("app.access")
error_logger = logging.getLogger("app.error")
audit_logger = logging.getLogger("app.audit")
security_logger = logging.getLogger("app.security")
perf_logger = logging.getLogger("app.performance")


def record_audit(
    action: str,
    entity_type: str,
    user_id: Optional[Any] = None,
    entity_id: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Standard function to record financial audit logs.
    Captures user action, entity type, target ID, and metadata.
    """
    audit_logger.info(
        f"AUDIT: [{action}] on [{entity_type}] (id={entity_id})",
        extra={
            "extra_data": {
                "action": action,
                "entity_type": entity_type,
                "entity_id": str(entity_id) if entity_id else None,
                "user_id": str(user_id) if user_id else user_id_ctx.get(),
                "metadata": metadata or {},
            }
        },
    )

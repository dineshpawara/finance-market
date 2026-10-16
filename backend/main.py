import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals to avoid charmap codec errors
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure the finance directory is in sys.path so imports work from any working directory
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from routes import news_router, market_router, trade_router, ws_router
from services import news_service
from services.seed_service import seed_default_user

# Centralized Structured Logging & Exception Management
from core.logging_config import setup_logging, app_logger, security_logger
from core.middleware import log_requests
from core.rate_limiter import limiter
from fastapi.exceptions import RequestValidationError
from core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Setup Logging (outputs to stdout for Docker/Alloy + rotating files in logs/)
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_to_file=os.getenv("LOG_TO_FILE", "true").lower() == "true",
)
logger = app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes startup tasks: Seeding default user & News pipeline."""
    logger.info("FastAPI server starting up...")

    # Idempotent seed for default user and trading wallet
    try:
        await asyncio.to_thread(seed_default_user)
    except Exception as e:
        logger.error(f"Error seeding default user during startup: {e}")

    try:
        asyncio.create_task(asyncio.to_thread(news_service.run_news_pipeline))
    except Exception as e:
        logger.error(f"Error launching startup news pipeline: {e}")
    yield
    logger.info("FastAPI server shutting down...")


app = FastAPI(
    title="Indian Stock Market Finance API",
    description="Developed By Dinesh Pawara",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# Attach SlowAPI Limiter state & middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Configure CORS Middleware for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach HTTP Request Logging & Tracing Middleware
app.middleware("http")(log_requests)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handles 429 Too Many Requests with unified error response & security logging."""
    rid = getattr(request.state, "request_id", "-")
    client_ip = request.client.host if request.client else "unknown"

    security_logger.warning(
        f"Rate limit exceeded: {request.method} {request.url.path} from IP {client_ip} ({exc.detail})"
    )

    return JSONResponse(
        status_code=429,
        headers={"Retry-After": "60"},
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and try again later.",
                "details": {"limit": str(exc.detail), "retry_after": 60},
            },
            "request_id": rid,
        },
    )


# Register Global Exception Handlers
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# API V1 routes========================================

from api.v1.router import api_v1_router

app.include_router(api_v1_router, prefix="/api/v1")
# =====================================================

# Include Routers
app.include_router(news_router)
app.include_router(market_router)
app.include_router(trade_router)
app.include_router(ws_router)


@app.get("/health")
def health_check():
    """Healthcheck endpoint for Docker Compose and container orchestrators."""
    return {"status": "healthy", "service": "finance_market_backend"}


@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Dinesh Pawara",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(BASE_DIR))

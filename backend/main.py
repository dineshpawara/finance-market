import asyncio
import logging
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

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import news_router, market_router, trade_router, ws_router
from services import news_service

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("finance_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes news pipeline in the background on server start and handles graceful shutdown."""
    logger.info("FastAPI server starting up...")
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
)

# Configure CORS Middleware for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows Vite dev server & production URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        "service": "Indian Stock Market Finance API (PostgreSQL + TimescaleDB + Redis)",
        "docs": "/docs",
        "endpoints": [
            "/api/news",
            "/api/v1/market/candles",
            "/api/v1/market/global",
            "/api/v1/market/nifty50",
            "/api/v1/market/option-chain",
            "/api/v1/wallet",
            "/api/v1/trades/order",
            "/api/v1/trades",
            "/ws/live",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(BASE_DIR))

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import news_router, market_router, trade_router, ws_router
from services import news_service

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("finance_backend")

app = FastAPI(
    title="Indian Stock Market Finance API",
    description="FastAPI Backend for Market Data, TimescaleDB Candles, Paper Trading Ledger & Redis Live Feeds",
    version="1.0.0"
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


@app.on_event("startup")
async def startup_event():
    """Initializes news pipeline in the background on server start."""
    logger.info("FastAPI server starting up...")
    try:
        asyncio.create_task(asyncio.to_thread(news_service.run_news_pipeline))
    except Exception as e:
        logger.error(f"Error launching startup news pipeline: {e}")


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
            "/ws/live"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
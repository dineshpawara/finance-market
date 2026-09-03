"""
Routes package initialization
"""
from .news_routes import router as news_router
from .market_routes import router as market_router
from .trade_routes import router as trade_router
from .websocket_routes import router as ws_router

__all__ = ["news_router", "market_router", "trade_router", "ws_router"]


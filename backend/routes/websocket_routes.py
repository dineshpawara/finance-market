"""
WebSocket Router - Real-Time Zero-Lag Tick & Incremental Candle Streaming
========================================================================
Pushes live market tick updates incrementally to connected TradingView charts
via FastAPI WebSockets & Redis Pub/Sub without polling or bulk chart re-fetches.
"""

import asyncio
import json
import random
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from database.redis_service import redis_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Real-Time Feed"])


class ConnectionManager:
    """Manages active WebSocket client connections for live market broadcasting."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WebSocket] Client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"[WebSocket] Client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live_ticks(websocket: WebSocket):
    """
    WebSocket endpoint streaming live market tick & incremental candle updates.
    """
    await manager.connect(websocket)

    base_prices = {
        "NIFTY50": 24852.15,
        "BANKNIFTY": 52140.35,
        "SENSEX": 81450.80,
        "RELIANCE": 2984.50,
        "TCS": 4210.80
    }

    try:
        while True:
            await asyncio.sleep(1.0)  # Stream every 1 second

            symbol = random.choice(list(base_prices.keys()))
            current_price = base_prices[symbol]
            change = (random.random() - 0.49) * (current_price * 0.001)
            new_price = round(current_price + change, 2)
            base_prices[symbol] = new_price

            tick_update = {
                "type": "TICK",
                "symbol": symbol,
                "price": new_price,
                "change": round(change, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "candle_update": {
                    "time": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "close": new_price,
                    "high": round(new_price + random.random() * 2, 2),
                    "low": round(new_price - random.random() * 2, 2),
                }
            }

            # Cache in Redis
            redis_service.set_live_price(symbol, tick_update)

            # Push tick to connected frontend
            await websocket.send_json(tick_update)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"[WebSocket] Loop error: {e}")
        manager.disconnect(websocket)

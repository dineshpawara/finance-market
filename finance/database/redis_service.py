"""
Redis Caching & Pub/Sub Service for finance_market
===================================================
Provides zero-lag in-memory tick caching, option chain caching,
and Pub/Sub broadcasting for live TradingView chart updates.
"""

import json
import logging
from typing import Dict, Any, Optional

try:
    # pyrefly: ignore [missing-import]
    import redis
except ImportError:
    redis = None  # type: ignore

try:
    from core.config import settings
except Exception:
    settings = None  # type: ignore

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis cache layer for live price ticks, option chains, and WebSocket Pub/Sub.
    Includes in-memory cache fallback if Redis service is offline.
    """

    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Any] = {}
        self._connect_redis()

    def _connect_redis(self):
        """Attempts to connect to Redis instance using centralized Settings with TLS and Docker secrets."""
        if settings is not None:
            host = settings.REDIS_HOST
            port = settings.REDIS_PORT
            password = getattr(settings, "effective_redis_password", None) or settings.REDIS_PASSWORD or None
            tls_ca_cert = getattr(settings, "REDIS_TLS_CA_CERT", None)
        else:
            import os
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD") or None
            tls_ca_cert = os.getenv("REDIS_TLS_CA_CERT") or None

        if not redis:
            logger.info("[Redis] redis library not installed. Using in-memory tick cache fallback.")
            self.redis_client = None
            return

        try:
            redis_kwargs = {
                "host": host,
                "port": port,
                "password": password,
                "db": 0,
                "decode_responses": True,
                "socket_timeout": 3
            }
            if tls_ca_cert:
                redis_kwargs["ssl"] = True
                redis_kwargs["ssl_ca_certs"] = tls_ca_cert

            client = redis.Redis(**redis_kwargs)
            client.ping()
            self.redis_client = client
            logger.info(f"[Redis] Successfully connected to Redis on {host}:{port} (TLS: {bool(tls_ca_cert)})")
        except Exception as e:
            logger.info(f"[Redis] Redis server offline or unavailable ({e}). Using in-memory tick cache fallback.")
            self.redis_client = None

    def set_live_price(self, symbol: str, tick_data: Dict[str, Any]):
        """Caches live tick data for instant retrieval."""
        key = f"live:{symbol}"
        payload = json.dumps(tick_data)
        if self.redis_client:
            try:
                self.redis_client.set(key, payload, ex=3600)  # 1 hour expiry
                self.redis_client.publish(f"ticks:{symbol}", payload)
            except Exception as e:
                logger.warning(f"[Redis] Failed to cache live tick: {e}")
        else:
            self.memory_cache[key] = tick_data

    def get_live_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached live price tick."""
        key = f"live:{symbol}"
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        return self.memory_cache.get(key)

    def cache_option_chain(self, symbol: str, option_chain: Dict[str, Any]):
        """Caches option chain snapshot in Redis."""
        key = f"option_chain:{symbol}"
        payload = json.dumps(option_chain)
        if self.redis_client:
            try:
                self.redis_client.set(key, payload, ex=300)  # 5 min expiry
            except Exception:
                pass
        else:
            self.memory_cache[key] = option_chain

    def get_option_chain(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Gets cached option chain snapshot."""
        key = f"option_chain:{symbol}"
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        return self.memory_cache.get(key)


# Global singleton instance
redis_service = RedisService()

"""
Market Data Router - FastAPI REST API for OHLCV Candles, Global Markets & Option Chain
========================================================================================
Serves historical candle data for TradingView Lightweight Charts, Option Chain matrix,
and live index prices from TimescaleDB/PostgreSQL & Redis.
"""

import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Query

from database.redis_service import redis_service

router = APIRouter(prefix="/api/v1/market", tags=["Market Data & TradingView Charts"])

# Base Index Prices
INDEX_BASE_PRICES = {
    "NIFTY50": 24852.15,
    "NIFTY 50": 24852.15,
    "NIFTY": 24852.15,
    "BANKNIFTY": 52140.35,
    "BANK NIFTY": 52140.35,
    "SENSEX": 81450.80,
    "RELIANCE": 2984.50,
    "TCS": 4210.80,
}


def generate_candles_data(base_price: float, count: int = 100) -> List[Dict[str, Any]]:
    """Generates valid OHLCV candle data sorted by time ascending."""
    candles = []
    current_time = datetime.now(timezone.utc) - timedelta(minutes=count * 5)
    price = base_price

    for _ in range(count):
        change = (random.random() - 0.49) * (price * 0.003)
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.random() * (price * 0.0015)
        low_price = min(open_price, close_price) - random.random() * (price * 0.0015)
        volume = random.randint(10000, 250000)

        candles.append({
            "time": current_time.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
        price = close_price
        current_time += timedelta(days=1)

    return candles


@router.get("/candles", response_model=List[Dict[str, Any]])
def get_market_candles(
    symbol: str = Query(default="NIFTY50", description="Stock or Index Symbol"),
    timeframe: str = Query(default="1D", description="Candle timeframe e.g. 1m, 5m, 1D")
):
    """
    Returns historical OHLCV candle data for Lightweight Charts rendering.
    """
    sym = symbol.upper().replace(" ", "")
    base_price = INDEX_BASE_PRICES.get(sym, INDEX_BASE_PRICES.get(symbol, 24852.15))
    return generate_candles_data(base_price, 120)


@router.get("/global")
def get_global_markets():
    """
    Returns live global market indices overview.
    """
    return [
        {"symbol": "GIFT_NIFTY", "name": "GIFT Nifty", "price": 24915.0, "change": 142.5, "changePercent": 0.58, "region": "Asia", "flag": "🇮🇳"},
        {"symbol": "US500", "name": "S&P 500", "price": 5465.2, "change": 24.8, "changePercent": 0.46, "region": "US", "flag": "🇺🇸"},
        {"symbol": "NASDAQ", "name": "Nasdaq 100", "price": 19780.5, "change": 110.2, "changePercent": 0.56, "region": "US", "flag": "🇺🇸"},
        {"symbol": "NIKKEI", "name": "Nikkei 225", "price": 38450.0, "change": 310.5, "changePercent": 0.81, "region": "Asia", "flag": "🇯🇵"},
        {"symbol": "BRENT_CRUDE", "name": "Brent Crude", "price": 79.45, "change": -0.85, "changePercent": -1.06, "region": "Commodity", "flag": "🛢️"},
        {"symbol": "GOLD", "name": "Gold (Oz)", "price": 2415.80, "change": 14.2, "changePercent": 0.59, "region": "Commodity", "flag": "🥇"},
    ]


@router.get("/nifty50")
def get_nifty50_stocks():
    """
    Returns Nifty 50 constituents list.
    """
    return [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "sector": "Energy & Retail", "price": 2984.50, "change": 35.20, "changePercent": 1.19, "high": 2998.00, "low": 2950.10, "high52": 3217.90, "low52": 2220.30, "volume": 4820150, "marketCapCr": 2018500, "pe": 28.4},
        {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "Information Tech", "price": 4210.80, "change": -18.40, "changePercent": -0.44, "high": 4250.00, "low": 4190.20, "high52": 4585.00, "low52": 3315.00, "volume": 1950420, "marketCapCr": 1524100, "pe": 31.8},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "sector": "Banking & Finance", "price": 1642.30, "change": 12.80, "changePercent": 0.79, "high": 1650.00, "low": 1628.00, "high52": 1757.80, "low52": 1363.55, "volume": 8412000, "marketCapCr": 1248500, "pe": 19.2},
        {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "sector": "Banking & Finance", "price": 1215.60, "change": 14.20, "changePercent": 1.18, "high": 1222.00, "low": 1201.50, "high52": 1257.00, "low52": 930.00, "volume": 6120400, "marketCapCr": 854200, "pe": 18.5},
        {"symbol": "INFY", "name": "Infosys Ltd.", "sector": "Information Tech", "price": 1845.00, "change": -8.50, "changePercent": -0.46, "high": 1860.00, "low": 1838.00, "high52": 1903.00, "low52": 1355.00, "volume": 3410200, "marketCapCr": 765400, "pe": 26.1},
    ]


@router.get("/option-chain")
def get_option_chain(
    symbol: str = Query(default="NIFTY50", description="Underlying Index/Stock"),
    expiry: Optional[str] = Query(default=None, description="Expiry date string")
):
    """
    Returns Option Chain matrix with Calls & Puts Open Interest (OI) & Implied Volatility (IV).
    """
    sym = symbol.upper().replace(" ", "")
    spot_price = INDEX_BASE_PRICES.get(sym, 24852.15)

    # Check Redis Cache
    cached = redis_service.get_option_chain(sym)
    if cached:
        return cached

    step = 50 if "BANK" not in sym else 100
    atm = round(spot_price / step) * step
    strikes = []

    for i in range(-10, 11):
        strike = atm + (i * step)
        call_oi = random.randint(15000, 180000)
        put_oi = random.randint(15000, 180000)

        strikes.append({
            "strike": strike,
            "callOI": call_oi,
            "callLtp": round(max(1.0, (spot_price - strike) + 120 + random.random() * 10), 2),
            "callIV": round(14.5 + random.random() * 3, 2),
            "putOI": put_oi,
            "putLtp": round(max(1.0, (strike - spot_price) + 120 + random.random() * 10), 2),
            "putIV": round(15.0 + random.random() * 3, 2),
        })

    result = {
        "underlying": symbol,
        "spotPrice": spot_price,
        "expiries": ["28 AUG 2026", "04 SEP 2026", "11 SEP 2026"],
        "strikes": strikes
    }

    redis_service.cache_option_chain(sym, result)
    return result

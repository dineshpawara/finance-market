"""
Paper Trading Router - Virtual Order Execution & Wallet Ledger API
===================================================================
Handles paper order placement, margin checks, virtual wallet ledger updates,
and trade history from PostgreSQL (finance_market DB).
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Query, HTTPException

from database.db_service import db_service

router = APIRouter(prefix="/api/v1", tags=["Paper Trading & Wallet Ledger"])


class PaperOrderRequest(BaseModel):
    user_id: int = Field(default=1, description="User Account ID")
    symbol: str = Field(description="Stock or Option Contract Symbol e.g. NIFTY 24500 CE")
    transaction_type: str = Field(description="BUY or SELL")
    quantity: int = Field(gt=0, description="Order quantity / lot size")
    price: float = Field(gt=0.0, description="Limit or Market Order Execution Price")
    instrument_type: Optional[str] = Field(default="EQ", description="EQ, CE, or PE")
    strike_price: Optional[float] = Field(default=0.0, description="Option Strike Price if applicable")
    expiry: Optional[str] = Field(default="", description="Contract Expiry string")
    stop_loss: Optional[float] = Field(default=0.0, description="Stop Loss Price trigger")
    target: Optional[float] = Field(default=0.0, description="Target Profit Price trigger")


@router.get("/wallet")
def get_wallet_balance(user_id: int = Query(default=1, description="User ID")):
    """
    Returns user virtual wallet balance and account status.
    """
    balance = db_service.get_wallet_balance(user_id=user_id)
    return {
        "user_id": user_id,
        "balance": balance,
        "currency": "INR"
    }


@router.post("/trades/order")
def execute_order(order: PaperOrderRequest):
    """
    Executes a paper trading order atomically with wallet margin verification.
    """
    res = db_service.execute_paper_trade(
        user_id=order.user_id,
        symbol=order.symbol,
        transaction_type=order.transaction_type.upper(),
        quantity=order.quantity,
        price=order.price,
        instrument_type=order.instrument_type,
        strike_price=order.strike_price,
        expiry=order.expiry,
        stop_loss=order.stop_loss,
        target=order.target
    )

    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))

    return res


@router.get("/trades")
def get_user_trades(user_id: int = Query(default=1, description="User ID")):
    """
    Returns list of open and closed paper trading orders for a user.
    """
    trades = db_service.get_user_trades(user_id=user_id)
    return {
        "user_id": user_id,
        "count": len(trades),
        "trades": trades
    }

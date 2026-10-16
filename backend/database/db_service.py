"""
Database Service - PostgreSQL Manager for finance_market
=========================================================
Handles user accounts, virtual wallets, paper trades, transactions,
and historical candle storage strictly using PostgreSQL (TimescaleDB).
All legacy SQLite fallbacks have been completely removed.
"""

import os
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
import psycopg2

logger = logging.getLogger(__name__)

# Configurable DB Settings strictly from centralized Settings without exposing credentials in code
try:
    from core.config import settings

    POSTGRES_DB = settings.POSTGRES_DB
    POSTGRES_USER = getattr(settings, "effective_postgres_user", None) or settings.POSTGRES_USER
    POSTGRES_PASSWORD = getattr(settings, "effective_postgres_password", None) or settings.POSTGRES_PASSWORD
    POSTGRES_HOST = settings.POSTGRES_HOST
    POSTGRES_PORT = settings.POSTGRES_PORT
    POSTGRES_SSLMODE = getattr(settings, "POSTGRES_SSLMODE", None)
    POSTGRES_SSLROOTCERT = getattr(settings, "POSTGRES_SSLROOTCERT", None)
    DEFAULT_WALLET_BALANCE = getattr(settings, "DEFAULT_WALLET_BALANCE", 1000000.00)
except Exception:
    settings = None
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_SSLMODE = os.getenv("POSTGRES_SSLMODE")
    POSTGRES_SSLROOTCERT = os.getenv("POSTGRES_SSLROOTCERT")
    DEFAULT_WALLET_BALANCE = float(os.getenv("DEFAULT_WALLET_BALANCE", "1000000.00"))


class DatabaseService:
    """
    Manages PostgreSQL (finance_market DB) connection for paper trading, virtual wallets, and candles.
    Strictly uses PostgreSQL; no SQLite fallback.
    """

    def __init__(self):
        self.pg_conn = None
        self._connect()
        if self.pg_conn:
            self._ensure_schema()

    def _connect(self):
        """Establishes or re-establishes connection to PostgreSQL database."""
        if not (POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD):
            logger.error("[DB] PostgreSQL credentials not configured in environment. Database unavailable.")
            self.pg_conn = None
            return

        try:
            connect_kwargs = {
                "dbname": POSTGRES_DB,
                "user": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "connect_timeout": 5,
            }
            if POSTGRES_SSLMODE:
                connect_kwargs["sslmode"] = POSTGRES_SSLMODE
            if POSTGRES_SSLROOTCERT and os.path.exists(POSTGRES_SSLROOTCERT):
                connect_kwargs["sslrootcert"] = POSTGRES_SSLROOTCERT

            self.pg_conn = psycopg2.connect(**connect_kwargs)
            logger.info(f"[DB] Successfully connected to PostgreSQL database '{POSTGRES_DB}'")
        except Exception as e:
            logger.error(f"[DB] Failed to connect to PostgreSQL database '{POSTGRES_DB}': {e}")
            self.pg_conn = None

    def _get_connection(self):
        """Returns active PostgreSQL connection, reconnecting if disconnected."""
        try:
            if self.pg_conn is None or self.pg_conn.closed:
                self._connect()
            else:
                with self.pg_conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            return self.pg_conn
        except Exception:
            logger.warning("[DB] PostgreSQL connection dropped; attempting reconnect...")
            self._connect()
            return self.pg_conn

    def _ensure_schema(self):
        """Ensures paper trading, wallet, and transaction tables exist in PostgreSQL."""
        conn = self._get_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                CREATE TABLE IF NOT EXISTS wallets (
                    user_id VARCHAR(100) PRIMARY KEY,
                    balance NUMERIC(20, 4) NOT NULL DEFAULT 1000000.00,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS paper_trades (
                    id VARCHAR(100) PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    instrument_type VARCHAR(20) NOT NULL DEFAULT 'EQ',
                    strike_price NUMERIC(15, 2) DEFAULT 0.00,
                    expiry VARCHAR(50) DEFAULT '',
                    transaction_type VARCHAR(10) NOT NULL,
                    quantity INTEGER NOT NULL,
                    entry_price NUMERIC(15, 2) NOT NULL,
                    entry_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    exit_price NUMERIC(15, 2),
                    exit_time TIMESTAMP WITH TIME ZONE,
                    status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
                    stop_loss NUMERIC(15, 2) DEFAULT 0.00,
                    target NUMERIC(15, 2) DEFAULT 0.00,
                    pnl NUMERIC(15, 2) DEFAULT 0.00
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    trade_id VARCHAR(100),
                    type VARCHAR(20) NOT NULL,
                    amount NUMERIC(20, 4) NOT NULL,
                    balance_after NUMERIC(20, 4) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS candles (
                    time TIMESTAMP WITH TIME ZONE NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    open NUMERIC(15, 2) NOT NULL,
                    high NUMERIC(15, 2) NOT NULL,
                    low NUMERIC(15, 2) NOT NULL,
                    close NUMERIC(15, 2) NOT NULL,
                    volume BIGINT NOT NULL,
                    PRIMARY KEY (symbol, time)
                );

                INSERT INTO wallets (user_id, balance) 
                VALUES ('1', %s) 
                ON CONFLICT (user_id) DO NOTHING;
                """,
                    (DEFAULT_WALLET_BALANCE,),
                )
                conn.commit()
                logger.info("[DB] PostgreSQL paper trading and wallet schema verified.")
        except Exception as e:
            conn.rollback()
            logger.error(f"[DB] Error ensuring PostgreSQL schema: {e}", exc_info=True)

    def get_wallet_balance(self, user_id: Any = 1) -> float:
        """Returns virtual wallet balance for user from PostgreSQL."""
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("Database connection unavailable. PostgreSQL is required.")

        uid = str(user_id)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM wallets WHERE user_id = %s;", (uid,))
                row = cur.fetchone()
                if row:
                    return float(row[0])

                # Provision initial wallet balance if user record does not exist
                cur.execute(
                    "INSERT INTO wallets (user_id, balance) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING RETURNING balance;",
                    (uid, DEFAULT_WALLET_BALANCE),
                )
                conn.commit()
                return float(DEFAULT_WALLET_BALANCE)
        except Exception as e:
            conn.rollback()
            logger.error(f"[DB] PostgreSQL query failed in get_wallet_balance ({e}).")
            raise

    def execute_paper_trade(
        self,
        user_id: Any,
        symbol: str,
        transaction_type: str,
        quantity: int,
        price: float,
        instrument_type: str = "EQ",
        strike_price: float = 0.0,
        expiry: str = "",
        stop_loss: float = 0.0,
        target: float = 0.0,
    ) -> Dict[str, Any]:
        """Atomically executes a paper trade and updates user wallet balance in PostgreSQL."""
        trade_id = f"trade_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        total_cost = price * quantity
        uid = str(user_id)

        conn = self._get_connection()
        if not conn:
            return {"status": "error", "message": "PostgreSQL database connection unavailable."}

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT balance FROM wallets WHERE user_id = %s FOR UPDATE;",
                    (uid,),
                )
                row = cur.fetchone()
                current_balance = float(row[0]) if row else DEFAULT_WALLET_BALANCE

                if not row:
                    cur.execute(
                        "INSERT INTO wallets (user_id, balance) VALUES (%s, %s);",
                        (uid, current_balance),
                    )

                if transaction_type == "BUY" and current_balance < total_cost:
                    return {
                        "status": "error",
                        "message": "Insufficient wallet funds for this order.",
                    }

                new_balance = (
                    current_balance - total_cost if transaction_type == "BUY" else current_balance + total_cost
                )

                cur.execute(
                    """
                    INSERT INTO paper_trades (id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, status, stop_loss, target)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'OPEN', %s, %s);
                    """,
                    (
                        trade_id,
                        uid,
                        symbol,
                        instrument_type,
                        strike_price,
                        expiry,
                        transaction_type,
                        quantity,
                        price,
                        stop_loss,
                        target,
                    ),
                )

                cur.execute(
                    "UPDATE wallets SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s;",
                    (new_balance, uid),
                )

                cur.execute(
                    """
                    INSERT INTO transactions (user_id, trade_id, type, amount, balance_after)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (uid, trade_id, transaction_type, total_cost, new_balance),
                )

                conn.commit()

                return {
                    "status": "success",
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "entry_price": price,
                    "wallet_balance": new_balance,
                }
        except Exception as e:
            conn.rollback()
            logger.error(f"[DB] PostgreSQL execute_paper_trade failed: {e}", exc_info=True)
            return {"status": "error", "message": f"Trade execution failed: {str(e)}"}

    def get_user_trades(self, user_id: Any = 1) -> List[Dict[str, Any]]:
        """Fetches all open and closed trades for a user from PostgreSQL."""
        conn = self._get_connection()
        if not conn:
            raise RuntimeError("Database connection unavailable. PostgreSQL is required.")

        uid = str(user_id)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, entry_time, status, stop_loss, target, pnl
                    FROM paper_trades WHERE user_id = %s ORDER BY entry_time DESC;
                    """,
                    (uid,),
                )
                rows = cur.fetchall()
                trades = []
                for r in rows:
                    trades.append(
                        {
                            "id": r[0],
                            "symbol": r[1],
                            "instrument_type": r[2],
                            "strike_price": float(r[3]) if r[3] is not None else 0.0,
                            "expiry": r[4] or "",
                            "transaction_type": r[5],
                            "quantity": int(r[6]),
                            "entry_price": float(r[7]),
                            "entry_time": r[8].isoformat() if hasattr(r[8], "isoformat") else str(r[8]),
                            "status": r[9],
                            "stop_loss": float(r[10]) if r[10] is not None else 0.0,
                            "target": float(r[11]) if r[11] is not None else 0.0,
                            "pnl": float(r[12]) if r[12] is not None else 0.0,
                        }
                    )
                return trades
        except Exception as e:
            conn.rollback()
            logger.error(f"[DB] PostgreSQL query failed in get_user_trades: {e}", exc_info=True)
            raise


# Global singleton instance
db_service = DatabaseService()

"""
Database Service - PostgreSQL & TimescaleDB Manager for finance_market
========================================================================
Handles user accounts, virtual wallets, paper trades, transactions,
and TimescaleDB historical candle queries.
"""

import os
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Configurable DB Settings strictly from centralized Settings without exposing credentials in code
try:
    from core.config import settings
    POSTGRES_DB = settings.POSTGRES_DB
    POSTGRES_USER = getattr(settings, "effective_postgres_user", None) or settings.POSTGRES_USER
    POSTGRES_PASSWORD = getattr(settings, "effective_postgres_password", None) or settings.POSTGRES_PASSWORD
    POSTGRES_HOST = settings.POSTGRES_HOST
    POSTGRES_PORT = settings.POSTGRES_PORT
    DEFAULT_WALLET_BALANCE = getattr(settings, "DEFAULT_WALLET_BALANCE", 1000000.00)
except Exception:
    settings = None
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    DEFAULT_WALLET_BALANCE = float(os.getenv("DEFAULT_WALLET_BALANCE", "1000000.00"))


class DatabaseService:
    """
    Manages PostgreSQL (finance_market DB) connection & SQLite fallback for paper trading & candles.
    """

    def __init__(self):
        self.use_postgres = False
        self.pg_conn = None
        self.sqlite_db_path = os.path.join(os.path.dirname(__file__), "finance_market.db")
        self._init_db()

    def _init_db(self):
        """Initializes PostgreSQL connection if credentials provided in .env/secrets, and ensures fallback schema."""
        self._init_sqlite_schema()

        if not (POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD):
            logger.info("[DB] PostgreSQL credentials not configured in environment. Using SQLite database.")
            self.use_postgres = False
            return

        try:
            import psycopg2
            connect_kwargs = {
                "dbname": POSTGRES_DB,
                "user": POSTGRES_USER,
                "password": POSTGRES_PASSWORD,
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "connect_timeout": 5
            }
            if settings and getattr(settings, "POSTGRES_SSLMODE", None):
                connect_kwargs["sslmode"] = settings.POSTGRES_SSLMODE
            if settings and getattr(settings, "POSTGRES_SSLROOTCERT", None):
                connect_kwargs["sslrootcert"] = settings.POSTGRES_SSLROOTCERT

            self.pg_conn = psycopg2.connect(**connect_kwargs)
            self.use_postgres = True
            logger.info(f"[DB] Successfully connected to PostgreSQL database '{POSTGRES_DB}'")
        except Exception as e:
            logger.info(f"[DB] PostgreSQL unavailable ({e}). Using SQLite database '{self.sqlite_db_path}'...")
            self.use_postgres = False

    def _init_sqlite_schema(self):
        """Creates SQLite tables if PostgreSQL server is offline."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS wallets (
            user_id INTEGER PRIMARY KEY,
            balance REAL NOT NULL DEFAULT 1000000.00,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS paper_trades (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            instrument_type TEXT NOT NULL DEFAULT 'EQ',
            strike_price REAL DEFAULT 0.00,
            expiry TEXT DEFAULT '',
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            entry_price REAL NOT NULL,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_price REAL,
            exit_time TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'OPEN',
            stop_loss REAL DEFAULT 0.00,
            target REAL DEFAULT 0.00,
            pnl REAL DEFAULT 0.00
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trade_id TEXT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS candles (
            time TEXT NOT NULL,
            symbol TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            PRIMARY KEY (symbol, time)
        );
        """)

        # Ensure default demo user exists
        cursor.execute("INSERT OR IGNORE INTO users (id, email, name) VALUES (1, 'trader@finance.market', 'Pro Trader')")
        cursor.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (1, ?)", (DEFAULT_WALLET_BALANCE,))

        conn.commit()
        conn.close()
        logger.info("[DB] SQLite database schema initialized with default demo user.")

    def get_wallet_balance(self, user_id: int = 1) -> float:
        """Returns virtual wallet balance for user with PostgreSQL & SQLite fallback."""
        if self.use_postgres and self.pg_conn:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("SELECT balance FROM wallets WHERE user_id = %s;", (user_id,))
                    row = cur.fetchone()
                    if row:
                        return float(row[0])
            except Exception as e:
                logger.warning(f"[DB] PostgreSQL query failed in get_wallet_balance ({e}). Falling back to SQLite.")
                try:
                    self.pg_conn.rollback()
                except Exception:
                    pass

        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else DEFAULT_WALLET_BALANCE

    def execute_paper_trade(
        self,
        user_id: int,
        symbol: str,
        transaction_type: str,
        quantity: int,
        price: float,
        instrument_type: str = "EQ",
        strike_price: float = 0.0,
        expiry: str = "",
        stop_loss: float = 0.0,
        target: float = 0.0
    ) -> Dict[str, Any]:
        """Atomically executes a paper trade and updates user wallet balance (PostgreSQL & SQLite fallback)."""
        trade_id = f"trade_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        total_cost = price * quantity

        if self.use_postgres and self.pg_conn:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("SELECT balance FROM wallets WHERE user_id = %s FOR UPDATE;", (user_id,))
                    row = cur.fetchone()
                    current_balance = float(row[0]) if row else DEFAULT_WALLET_BALANCE

                    if transaction_type == "BUY" and current_balance < total_cost:
                        return {"status": "error", "message": "Insufficient wallet funds for this order."}

                    new_balance = current_balance - total_cost if transaction_type == "BUY" else current_balance + total_cost

                    cur.execute("""
                        INSERT INTO paper_trades (id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, status, stop_loss, target)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'OPEN', %s, %s);
                    """, (trade_id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, price, stop_loss, target))

                    cur.execute("UPDATE wallets SET balance = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s;", (new_balance, user_id))

                    cur.execute("""
                        INSERT INTO transactions (user_id, trade_id, type, amount, balance_after)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (user_id, trade_id, transaction_type, total_cost, new_balance))

                    self.pg_conn.commit()

                    return {
                        "status": "success",
                        "trade_id": trade_id,
                        "symbol": symbol,
                        "transaction_type": transaction_type,
                        "quantity": quantity,
                        "entry_price": price,
                        "wallet_balance": new_balance
                    }
            except Exception as e:
                logger.warning(f"[DB] PostgreSQL execute_paper_trade failed ({e}). Rolling back and falling back to SQLite.")
                try:
                    self.pg_conn.rollback()
                except Exception:
                    pass

        # SQLite Fallback
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        current_balance = row[0] if row else DEFAULT_WALLET_BALANCE

        if transaction_type == "BUY" and current_balance < total_cost:
            conn.close()
            return {"status": "error", "message": "Insufficient wallet funds for this order."}

        new_balance = current_balance - total_cost if transaction_type == "BUY" else current_balance + total_cost

        cursor.execute("""
            INSERT INTO paper_trades (id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, status, stop_loss, target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
        """, (trade_id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, price, stop_loss, target))

        cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_balance, user_id))

        cursor.execute("""
            INSERT INTO transactions (user_id, trade_id, type, amount, balance_after)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, trade_id, transaction_type, total_cost, new_balance))

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "trade_id": trade_id,
            "symbol": symbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "entry_price": price,
            "wallet_balance": new_balance
        }

    def get_user_trades(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """Fetches all open and closed trades for a user with PostgreSQL & SQLite fallback."""
        if self.use_postgres and self.pg_conn:
            try:
                with self.pg_conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, entry_time, status, stop_loss, target, pnl
                        FROM paper_trades WHERE user_id = %s ORDER BY entry_time DESC;
                    """, (user_id,))
                    rows = cur.fetchall()
                    trades = []
                    for r in rows:
                        trades.append({
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
                            "pnl": float(r[12]) if r[12] is not None else 0.0
                        })
                    return trades
            except Exception as e:
                logger.warning(f"[DB] PostgreSQL query failed in get_user_trades ({e}). Falling back to SQLite.")
                try:
                    self.pg_conn.rollback()
                except Exception:
                    pass

        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, entry_time, status, stop_loss, target, pnl
            FROM paper_trades WHERE user_id = ? ORDER BY entry_time DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        trades = []
        for r in rows:
            trades.append({
                "id": r[0],
                "symbol": r[1],
                "instrument_type": r[2],
                "strike_price": r[3],
                "expiry": r[4],
                "transaction_type": r[5],
                "quantity": r[6],
                "entry_price": r[7],
                "entry_time": r[8],
                "status": r[9],
                "stop_loss": r[10],
                "target": r[11],
                "pnl": r[12]
            })
        return trades


# Global singleton instance
db_service = DatabaseService()


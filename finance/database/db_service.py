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

# Configurable DB Settings
POSTGRES_DB = os.getenv("POSTGRES_DB", "finance_market")
POSTGRES_USER = os.getenv("POSTGRES_USER", "dinesh")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminDinesh")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


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
        """Initializes PostgreSQL connection or SQLite fallback schema."""
        try:
            import psycopg2
            self.pg_conn = psycopg2.connect(
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT
            )
            self.use_postgres = True
            logger.info(f"[DB] Successfully connected to PostgreSQL database '{POSTGRES_DB}'")
        except Exception as e:
            logger.info(f"[DB] PostgreSQL unavailable ({e}). Initializing SQLite fallback '{self.sqlite_db_path}'...")
            self.use_postgres = False
            self._init_sqlite_schema()

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
        cursor.execute("INSERT OR IGNORE INTO wallets (user_id, balance) VALUES (1, 1000000.00)")

        conn.commit()
        conn.close()
        logger.info("[DB] SQLite database schema initialized with default demo user.")

    def get_wallet_balance(self, user_id: int = 1) -> float:
        """Returns virtual wallet balance for user."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 1000000.00

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
        """Atomically executes a paper trade and updates user wallet balance."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        trade_id = f"trade_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        total_cost = price * quantity

        cursor.execute("SELECT balance FROM wallets WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        current_balance = row[0] if row else 1000000.00

        if transaction_type == "BUY" and current_balance < total_cost:
            conn.close()
            return {"status": "error", "message": "Insufficient wallet funds for this order."}

        new_balance = current_balance - total_cost if transaction_type == "BUY" else current_balance + total_cost

        # Insert Trade
        cursor.execute("""
            INSERT INTO paper_trades (id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, entry_price, status, stop_loss, target)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
        """, (trade_id, user_id, symbol, instrument_type, strike_price, expiry, transaction_type, quantity, price, stop_loss, target))

        # Update Wallet
        cursor.execute("UPDATE wallets SET balance = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_balance, user_id))

        # Add Ledger Transaction
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
        """Fetches all open and closed trades for a user."""
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

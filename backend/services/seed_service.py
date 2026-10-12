"""
Database Seed Service
=====================
Idempotent seeding for Finance Market Platform.
Ensures default administrator/trader accounts, paper trading wallets,
and audit logs are established without duplication or schema violations.
"""

import secrets
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.logging_config import app_logger
from core.security import hash_password
from database.session import SessionLocal
from models.user import User
from models.trading_account import TradingAccount
from models.account_balance import AccountBalance
from models.audit_log import AuditLog


def _generate_account_number(email: str) -> str:
    """Generates a unique deterministic-format trading account number."""
    user_prefix = email.split("@")[0].upper()[:6].replace(".", "")
    random_hex = secrets.token_hex(2).upper()
    return f"TRD-{user_prefix}-{random_hex}"


def seed_default_user(db: Optional[Session] = None) -> Optional[User]:
    """
    Idempotently seeds the default user from environment variables into PostgreSQL.

    Guarantees:
    - Zero duplication (unique index on email respected)
    - Password is encrypted using bcrypt before storage
    - Automatically provisions paper trading wallet (default balance: 1,000,000 INR)
    - Records financial audit log
    - Safe to execute repeatedly on server boot or CLI
    """
    should_close_session = False
    if db is None:
        db = SessionLocal()
        should_close_session = True

    try:
        email = settings.seed_user_email
        raw_password = settings.seed_user_password
        name = settings.seed_user_name or "Default User"
        is_active = settings.seed_user_is_active

        # Security Guard: Skip cleanly if credentials are not configured in .env
        if not email or not raw_password:
            app_logger.warning(
                "[SEED] Default user credentials (EMAIL or PASSWORD) not configured in .env. Skipping default user creation."
            )
            return None

        email = email.strip().lower()
        name = name.strip()

        # 1. Idempotency Check: Query existing user by unique email
        stmt = select(User).where(User.email == email)
        existing_user = db.scalar(stmt)

        if existing_user:
            app_logger.info(
                f"[SEED] Default user '{email}' already exists (ID: {existing_user.id}). Skipping creation."
            )
            return existing_user

        # 2. Hash Password securely using bcrypt
        hashed_password = hash_password(raw_password)
        now = datetime.now(timezone.utc)

        # 3. Create User ORM instance
        new_user = User(
            id=uuid.uuid4(),
            name=name,
            email=email,
            password_hash=hashed_password,
            password_changed_at=now,
            password_expires_at=now + timedelta(days=30),
            is_active=is_active,
        )
        db.add(new_user)
        db.flush()  # Flushes to get new_user.id for foreign keys

        # 4. Provision default Paper Trading Account
        account_number = _generate_account_number(email)
        trading_account = TradingAccount(
            id=uuid.uuid4(),
            user_id=new_user.id,
            account_number=account_number,
            currency=getattr(settings, "CURRENCY", "INR"),
            status="ACTIVE",
        )
        db.add(trading_account)
        db.flush()

        # 5. Provision Initial Virtual Trading Balance
        wallet_balance = Decimal(str(getattr(settings, "DEFAULT_WALLET_BALANCE", 1000000.00)))
        initial_balance = AccountBalance(
            id=uuid.uuid4(),
            account_id=trading_account.id,
            available_balance=wallet_balance,
            blocked_balance=Decimal("0.0"),
            realized_pnl=Decimal("0.0"),
            unrealized_pnl=Decimal("0.0"),
        )
        db.add(initial_balance)

        # 6. Record System Audit Log for Compliance
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=new_user.id,
            action="SYSTEM_DEFAULT_USER_SEEDED",
            entity_type="user",
            entity_id=new_user.id,
            metadata_={
                "email": new_user.email,
                "name": new_user.name,
                "account_number": account_number,
                "initial_wallet": float(wallet_balance),
            },
        )
        db.add(audit_entry)

        # 7. Commit atomic transaction
        db.commit()
        db.refresh(new_user)

        app_logger.info(
            f"[SEED] Successfully seeded default user '{new_user.email}' with trading account '{account_number}'."
        )
        return new_user

    except Exception as e:
        db.rollback()
        app_logger.error(f"[SEED] Error seeding default user: {str(e)}", exc_info=True)
        raise
    finally:
        if should_close_session:
            db.close()

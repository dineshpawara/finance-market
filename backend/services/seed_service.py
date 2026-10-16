"""
Database Seed Service
=====================
Idempotent seeding for Finance Market Platform.
Ensures default administrator/trader accounts, paper trading wallets,
and audit logs are established without duplication or schema violations.
"""

import secrets
import string
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import settings
from core.logging_config import app_logger, security_logger
from core.security import hash_password
from database.session import SessionLocal
from models.user import User
from models.trading_account import TradingAccount
from models.account_balance import AccountBalance
from models.audit_log import AuditLog
from models.master_key import MasterKey


def generate_master_key() -> str:
    """
    Generates a cryptographically secure random Master Key in the format:
    XXXX-XXXX-XXXX-XXXX (4 blocks of 4 alphanumeric uppercase characters).
    Uses Python's secrets module (CSPRNG) with uppercase letters and digits.
    Provides ~82.7 bits of cryptographic entropy.
    """
    charset = string.ascii_uppercase + string.digits
    blocks = ["".join(secrets.choice(charset) for _ in range(4)) for _ in range(4)]
    return "-".join(blocks)


def _generate_account_number(email: str) -> str:
    """Generates a unique deterministic-format trading account number."""
    user_prefix = email.split("@")[0].upper()[:6].replace(".", "")
    random_hex = secrets.token_hex(2).upper()
    return f"TRD-{user_prefix}-{random_hex}"


def seed_master_key_for_user(user: User, db: Session) -> Tuple[Optional[MasterKey], Optional[str]]:
    """
    Idempotently seeds the master security authorization key for the user into PostgreSQL.

    Guarantees:
    - If active master key already exists, skips generation without duplication.
    - If none exists, generates a cryptographically random key formatted as 'XXXX-XXXX-XXXX-XXXX'.
    - Encrypted using bcrypt (12 salt rounds) before storage in master_keys table.
    - Plaintext key is never persisted in database or files.
    - Audited via AuditLog for regulatory and security compliance.

    Returns:
        Tuple of (MasterKey ORM instance, raw_key_string_if_newly_generated)
    """
    # 1. Idempotency Check: Fetch active (un-used) master keys for this user
    stmt = select(MasterKey).where(
        MasterKey.user_id == user.id,
        MasterKey.used_at.is_(None),
    )
    existing_key = db.scalar(stmt)
    if existing_key:
        app_logger.info(
            f"[SEED] Active master key for user '{user.email}' already exists in PostgreSQL (ID: {existing_key.id}). Skipping creation."
        )
        return existing_key, None

    # 2. Cryptographically generate fresh random master key (or read configured override if any)
    configured_key = getattr(settings, "seed_master_key", None)
    if configured_key and str(configured_key).strip():
        raw_key = str(configured_key).strip().upper()
    else:
        raw_key = generate_master_key()

    # 3. Encrypt/Hash the master key using bcrypt (12 rounds)
    hashed_key = hash_password(raw_key)
    now = datetime.now(timezone.utc)

    # 4. Create MasterKey entity
    master_key_record = MasterKey(
        id=uuid.uuid4(),
        user_id=user.id,
        key_hash=hashed_key,
        used_at=None,
        expires_at=None,
        created_at=now,
    )
    db.add(master_key_record)
    db.flush()

    # 5. Record compliance audit log
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        user_id=user.id,
        action="SYSTEM_MASTER_KEY_SEEDED",
        entity_type="master_key",
        entity_id=master_key_record.id,
        metadata_={
            "user_id": str(user.id),
            "email": user.email,
            "key_format": "XXXX-XXXX-XXXX-XXXX",
            "algorithm": "bcrypt_12_rounds",
            "status": "ACTIVE",
            "timestamp": now.isoformat(),
        },
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(master_key_record)

    security_logger.info(
        f"[SECURITY] Generated new Master Security Key for user '{user.email}' (ID: {master_key_record.id}). Key securely hashed in DB."
    )
    return master_key_record, raw_key


def seed_default_user(db: Optional[Session] = None) -> Tuple[Optional[User], Optional[str]]:
    """
    Idempotently seeds the default user from environment variables into PostgreSQL.

    Guarantees:
    - Zero duplication (unique index on email respected)
    - Password is encrypted using bcrypt before storage
    - Automatically provisions paper trading wallet (default balance: 1,000,000 INR)
    - Records financial audit log
    - Seeds authorized Master Key for single-user emergency recovery
    - Safe to execute repeatedly on server boot or CLI

    Returns:
        Tuple of (User ORM instance, raw_master_key_if_newly_generated)
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
            return None, None

        email = email.strip().lower()
        name = name.strip()

        # 1. Idempotency Check: Query existing user by unique email
        stmt = select(User).where(User.email == email)
        existing_user = db.scalar(stmt)

        if existing_user:
            app_logger.info(
                f"[SEED] Default user '{email}' already exists (ID: {existing_user.id}). Skipping user creation."
            )
            # Ensure Master Key is seeded for existing user as well
            _, raw_master_key = seed_master_key_for_user(existing_user, db)
            return existing_user, raw_master_key

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

        # 6. Record System Audit Log for User Creation
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

        # 7. Commit atomic transaction for User and Paper Trading
        db.commit()
        db.refresh(new_user)

        # 8. Seed Master Security Key for Forget Password recovery
        _, raw_master_key = seed_master_key_for_user(new_user, db)

        app_logger.info(
            f"[SEED] Successfully seeded default user '{new_user.email}' with trading account '{account_number}'."
        )
        return new_user, raw_master_key

    except Exception as e:
        db.rollback()
        app_logger.error(f"[SEED] Error seeding default user: {str(e)}", exc_info=True)
        raise
    finally:
        if should_close_session:
            db.close()

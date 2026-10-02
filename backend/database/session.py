"""
Database Session Management
===========================
Configures SQLAlchemy engine, connection pooling, and FastAPI get_db dependency.
Reads connection URL securely from centralized Settings without exposing credentials in code.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from core.config import settings

# Create engine using centralized settings
engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,      # Automatically reconnects dropped DB connections
    pool_size=10,            # Maintains 10 persistent connections in pool
    max_overflow=20          # Allows up to 20 temporary burst connections
)

# Session factory for handling unit-of-work transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency that yields a database session per HTTP request
    and guarantees proper closure in a finally block to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

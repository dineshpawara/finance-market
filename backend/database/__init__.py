"""
Database Package for Finance Market
===================================
Consolidated database layer providing:
- SQLAlchemy 2.0 Base & session dependency (Base, engine, SessionLocal, get_db)
- Virtual paper trading & ledger service (db_service, DatabaseService)
- Redis live tick caching & Pub/Sub service (redis_service, RedisService)
"""

from database.base import Base, POSTGRES_NAMING_CONVENTION
from database.session import engine, SessionLocal, get_db
from database.db_service import db_service, DatabaseService
from database.redis_service import redis_service, RedisService

__all__ = [
    "Base",
    "POSTGRES_NAMING_CONVENTION",
    "engine",
    "SessionLocal",
    "get_db",
    "db_service",
    "DatabaseService",
    "redis_service",
    "RedisService",
]

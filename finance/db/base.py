"""
SQLAlchemy Declarative Base
===========================
Central ORM Registry for all database models in the finance platform.
Configures standardized constraint naming conventions for Alembic & PostgreSQL.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Professional constraint naming conventions for PostgreSQL & Alembic migrations.
# This prevents unnamed constraints that cause issues during schema alterations/drops.
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    Parent class for all SQLAlchemy 2.0 models.
    All application entities (User, Wallet, Trade, etc.) inherit from this Base.
    """
    # Attach standardized naming conventions to the metadata catalog
    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

    def __repr__(self) -> str:
        """
        Generic string representation for any inheriting model,
        displaying primary key and key attributes for easy logging.
        """
        class_name = self.__class__.__name__
        attrs = [
            f"{key}={value!r}"
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        ]
        return f"<{class_name}({', '.join(attrs)})>"

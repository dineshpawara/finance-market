"""
Repository package initialization
"""

from .news_repository import NewsRepository, news_repository
from .user_repository import UserRepository
from .master_key_repository import MasterKeyRepository

__all__ = ["NewsRepository", "news_repository", "UserRepository", "MasterKeyRepository"]

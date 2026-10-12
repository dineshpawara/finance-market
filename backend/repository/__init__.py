"""
Repository package initialization
"""

from .news_repository import NewsRepository, news_repository
from .user_repository import UserRepository

__all__ = ["NewsRepository", "news_repository", "UserRepository"]

"""
Services package initialization
"""
from .news_service import NewsService, news_service, RSS_FEEDS

__all__ = ["NewsService", "news_service", "RSS_FEEDS"]

"""
Repository Layer - News & Sentiment Cache Repository
===================================================
Manages in-memory and file-based JSON caching of news articles and AI sentiment outputs.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "news_cache.json")


class NewsRepository:
    """
    Repository for managing stored news items with sentiment tags.
    """

    def __init__(self, cache_filepath: str = CACHE_FILE):
        self.cache_filepath = os.path.abspath(cache_filepath)
        self._news_store: List[Dict[str, Any]] = []
        self.load_from_disk()

    def load_from_disk(self) -> None:
        """Loads cached news items from JSON disk storage if present."""
        if os.path.exists(self.cache_filepath):
            try:
                with open(self.cache_filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._news_store = data
                        logger.info(f"Loaded {len(self._news_store)} cached news articles from disk.")
            except Exception as e:
                logger.error(f"Failed loading news cache from disk: {e}")
                self._news_store = []

    def save_to_disk(self) -> None:
        """Saves current news items to JSON disk storage."""
        try:
            with open(self.cache_filepath, "w", encoding="utf-8") as f:
                json.dump(self._news_store, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed saving news cache to disk: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        return self._news_store

    def get_news(
        self,
        limit: int = 50,
        sentiment: Optional[str] = None,
        source: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves stored news filtered by sentiment, source, or search query."""
        results = self._news_store

        if sentiment and sentiment.upper() != "ALL":
            s_upper = sentiment.upper()
            # Map sentiment aliases (e.g. positive/BULLISH, negative/BEARISH, neutral/NEUTRAL)
            if s_upper in ["BULLISH", "POSITIVE"]:
                results = [item for item in results if item.get("sentiment", "").upper() in ["BULLISH", "POSITIVE"]]
            elif s_upper in ["BEARISH", "NEGATIVE"]:
                results = [item for item in results if item.get("sentiment", "").upper() in ["BEARISH", "NEGATIVE"]]
            else:
                results = [item for item in results if item.get("sentiment", "").upper() in ["NEUTRAL"]]

        if source:
            results = [item for item in results if source.lower() in item.get("source", "").lower()]

        if search_query:
            q = search_query.lower()
            results = [
                item for item in results if q in item.get("title", "").lower() or q in item.get("summary", "").lower()
            ]

        return results[:limit]

    def update_news_store(self, fresh_news: List[Dict[str, Any]]) -> None:
        """
        Updates the repository store with newly fetched and classified articles.
        Preserves existing items while avoiding duplicates by title.
        """
        existing_titles = {n["title"].lower().strip() for n in self._news_store if "title" in n}

        new_items = []
        for item in fresh_news:
            t = item.get("title", "").lower().strip()
            if t and t not in existing_titles:
                existing_titles.add(t)
                new_items.append(item)

        # Prepend newest items
        self._news_store = new_items + self._news_store
        # Limit total cache size to 200 articles
        self._news_store = self._news_store[:200]
        self.save_to_disk()

    def get_count(self) -> int:
        return len(self._news_store)


# Global singleton instance of NewsRepository
news_repository = NewsRepository()

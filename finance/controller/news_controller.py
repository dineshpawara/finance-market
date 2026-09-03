"""
Controller Layer - News Controller
====================================
Orchestrates requests between API Routes, NewsService, and NewsRepository.
Calculates overall market sentiment scores and structures responses.
"""

from typing import Dict, List, Any, Optional
from services.news_service import news_service
from repository.news_repository import news_repository


class NewsController:
    """
    Controller layer for Indian Stock Market News & FinBERT sentiment data.
    """

    def get_top_news(
        self,
        limit: int = 20,
        sentiment: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetches news articles. Triggers fresh pipeline fetch if repository is empty
        or if force_refresh is requested.
        """
        if force_refresh or news_repository.get_count() == 0:
            news_service.run_news_pipeline()

        return news_repository.get_news(
            limit=limit,
            sentiment=sentiment,
            source=source,
            search_query=search
        )

    def get_sentiment_summary(self) -> Dict[str, Any]:
        """
        Calculates overall market sentiment score based on current cached news.
        Returns score (0-100), label ('BULLISH', 'BEARISH', 'NEUTRAL'), and breakdown counts.
        """
        news_items = news_repository.get_news(limit=100)
        if not news_items:
            # If no cached items, try running pipeline once
            news_items = news_service.run_news_pipeline()

        if not news_items:
            return {"score": 50, "label": "NEUTRAL", "count": 0, "bullish": 0, "bearish": 0, "neutral": 0}

        bullish_count = sum(1 for n in news_items if n.get("sentiment") in ["BULLISH", "positive"])
        bearish_count = sum(1 for n in news_items if n.get("sentiment") in ["BEARISH", "negative"])
        neutral_count = len(news_items) - bullish_count - bearish_count

        total = len(news_items)
        score = round((bullish_count / total) * 100) if total > 0 else 50

        if score >= 60:
            label = "BULLISH"
        elif score <= 40:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        return {
            "score": score,
            "label": label,
            "count": total,
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count
        }

    def trigger_refresh(self, recency_minutes: int = 600) -> Dict[str, Any]:
        """Triggers manual feed refresh and sentiment re-classification."""
        updated = news_service.run_news_pipeline(recency_minutes=recency_minutes)
        summary = self.get_sentiment_summary()
        return {
            "status": "success",
            "message": f"Successfully refreshed feeds and classified {len(updated)} articles.",
            "total_articles": len(updated),
            "sentiment_summary": summary
        }

    def validate_feeds(self) -> Dict[str, Any]:
        """Validates all RSS feed sources."""
        return news_service.validate_rss_feeds()


# Global singleton instance of NewsController
news_controller = NewsController()

"""
Routes Layer - FastAPI Router for News & FinBERT Sentiment
===========================================================
Defines HTTP endpoints for news feed retrieval, sentiment statistics,
manual RSS refreshes, and feed diagnostics.
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any

from controller.news_controller import news_controller

router = APIRouter(prefix="/api/v1/news", tags=["News & Sentiment"])


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_news(
    limit: int = Query(default=20, ge=1, le=100),
    sentiment: Optional[str] = Query(default=None, description="Filter by sentiment: BULLISH, BEARISH, NEUTRAL, ALL"),
    source: Optional[str] = Query(default=None, description="Filter by source name"),
    q: Optional[str] = Query(default=None, description="Search query string"),
    refresh: bool = Query(default=False, description="Force manual refresh of RSS feeds"),
):
    """
    Returns latest Indian Stock Market headlines with FinBERT sentiment classification.
    """
    return news_controller.get_top_news(
        limit=limit, sentiment=sentiment, source=source, search=q, force_refresh=refresh
    )


@router.get("/sentiment-summary")
def get_sentiment_summary():
    """
    Returns overall market sentiment score (0-100), label (BULLISH/BEARISH/NEUTRAL),
    and article breakdown counts.
    """
    return news_controller.get_sentiment_summary()


@router.post("/refresh")
def refresh_news_feeds(recency_minutes: int = Query(default=600, ge=15, le=2880)):
    """
    Triggers an immediate fetch of all RSS feeds and runs FinBERT sentiment analysis.
    """
    return news_controller.trigger_refresh(recency_minutes=recency_minutes)


@router.get("/validate-feeds")
def validate_rss_feeds():
    """
    Validates health and accessibility of all configured RSS feed sources.
    """
    return news_controller.validate_feeds()

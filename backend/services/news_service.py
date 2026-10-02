"""
Service Layer - Indian Stock Market News Sentiment Service
============================================================
Fetches RSS feeds, handles recency window filtering, deduplication,
and orchestrates AI model sentiment classification.
"""

import calendar
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Any

# pyrefly: ignore [missing-import]
import feedparser

from AI_model.sentiment_model import classify_news_titles
from repository.news_repository import news_repository

logger = logging.getLogger(__name__)

# RSS Feed sources dictionary
RSS_FEEDS = {
    # --- Indian markets / corporates ---
    "Economic Times - Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Economic Times - Business": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "Economic Times - Stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
    "Economic Times - Economy": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
    "Moneycontrol - Business": "https://www.moneycontrol.com/rss/business.xml",
    "Moneycontrol - Markets": "https://www.moneycontrol.com/rss/marketreports.xml",
    "Moneycontrol - Latest News": "https://www.moneycontrol.com/rss/latestnews.xml",
    "Moneycontrol - Economy": "https://www.moneycontrol.com/rss/economy.xml",
    "LiveMint - Markets": "https://www.livemint.com/rss/markets",
    "LiveMint - Industry": "https://www.livemint.com/rss/industry",
    "CNBC-TV18 - Market": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market.xml",
    # --- Global cues ---
    "CNBC - World": "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    # --- Reuters / Bloomberg workaround via Google News ---
    "Reuters (via Google News)": "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com+(markets+OR+RBI+OR+India+OR+Fed)&hl=en-IN&gl=IN&ceid=IN:en",
    "Bloomberg (via Google News)": "https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com+(India+OR+markets+OR+Fed+OR+RBI)&hl=en-IN&gl=IN&ceid=IN:en",
    # --- Keyword-based catch-all ---
    "Google News - Nifty50/Sensex": "https://news.google.com/rss/search?q=when:24h+(Nifty50+OR+Sensex+OR+%22Indian+stock+market%22)&hl=en-IN&gl=IN&ceid=IN:en",
    "Google News - RBI/FII": "https://news.google.com/rss/search?q=when:24h+(RBI+policy+OR+FII+outflow+OR+FII+inflow)&hl=en-IN&gl=IN&ceid=IN:en",
}

DEFAULT_RECENCY_MINUTES = 600  # Default window to keep articles (e.g. 10 hours for trading sessions)


class NewsService:
    """
    Business logic layer for RSS news fetching & FinBERT sentiment analysis.
    """

    def validate_rss_feeds(self) -> Dict[str, Any]:
        """Checks every RSS feed URL and returns status breakdown."""
        logger.info("Validating RSS feed endpoints...")
        results = {}
        for name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                if feed.bozo and not feed.entries:
                    results[name] = {"status": "DEAD", "url": url, "entries": 0}
                else:
                    results[name] = {
                        "status": "OK",
                        "url": url,
                        "entries": len(feed.entries),
                    }
            except Exception as e:
                results[name] = {"status": "ERROR", "url": url, "error": str(e)}
        return results

    def fetch_all_rss_news(self) -> List[Dict[str, Any]]:
        """Fetches raw news articles from all defined RSS feeds."""
        all_news = []
        for source_name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:30]:  # Top 30 items per source
                    raw_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)

                    epoch_utc = calendar.timegm(raw_struct) if isinstance(raw_struct, time.struct_time) else None

                    title = str(entry.get("title", "")).strip()
                    link = str(entry.get("link", ""))
                    published = str(entry.get("published", entry.get("updated", "")))
                    summary = str(entry.get("summary", entry.get("description", ""))).strip()
                    # Clean HTML tags from summary if present
                    if "<" in summary and ">" in summary:
                        import re

                        summary = re.sub(r"<[^>]+>", "", summary).strip()

                    all_news.append(
                        {
                            "id": f"{source_name}_{hash(title)}",
                            "source": source_name,
                            "title": title,
                            "summary": summary[:250] + "..." if len(summary) > 250 else summary,
                            "link": link,
                            "published": published,
                            "published_epoch_utc": epoch_utc,
                        }
                    )
            except Exception as e:
                logger.error(f"[RSS] Failed to fetch from {source_name}: {e}")
        return all_news

    def filter_recent_news(
        self, news_list: List[Dict[str, Any]], minutes: int = DEFAULT_RECENCY_MINUTES
    ) -> List[Dict[str, Any]]:
        """Filters articles published within the last `minutes` window."""
        now_utc = datetime.now(timezone.utc).timestamp()
        cutoff = now_utc - (minutes * 60)

        recent = []
        for item in news_list:
            epoch = item.get("published_epoch_utc")
            # If timestamp exists and within cutoff, keep it. If no epoch timestamp, keep if title is valid.
            if epoch is not None:
                if epoch >= cutoff:
                    recent.append(item)
            else:
                recent.append(item)

        return recent

    def run_news_pipeline(self, recency_minutes: int = DEFAULT_RECENCY_MINUTES) -> List[Dict[str, Any]]:
        """
        Executes complete news sentiment pipeline:
        1. Fetch RSS feeds
        2. Deduplicate by title
        3. Recency filter
        4. FinBERT AI sentiment classification
        5. Update Repository cache
        """
        logger.info(f"Running news sentiment pipeline (recency={recency_minutes} min)...")

        raw_news = self.fetch_all_rss_news()
        if not raw_news:
            logger.warning("No raw news fetched from RSS feeds.")
            return news_repository.get_news(limit=50)

        # Deduplicate by title
        seen_titles = set()
        deduped = []
        for item in raw_news:
            t = item["title"].lower().strip()
            if t and t not in seen_titles:
                seen_titles.add(t)
                deduped.append(item)

        # Recency filter
        fresh_news = self.filter_recent_news(deduped, minutes=recency_minutes)
        if not fresh_news:
            logger.info(f"No fresh headlines in last {recency_minutes} minutes. Using all deduped news.")
            fresh_news = deduped[:40]

        # Extract titles for AI Model classification
        titles = [n["title"] for n in fresh_news]
        sentiments = classify_news_titles(titles)

        # Attach AI sentiment output
        for idx, item in enumerate(fresh_news):
            if idx < len(sentiments):
                res = sentiments[idx]
                raw_sent = res["sentiment"].lower()
                # Normalize label to standard uppercase format for frontend
                if raw_sent == "positive":
                    item["sentiment"] = "BULLISH"
                elif raw_sent == "negative":
                    item["sentiment"] = "BEARISH"
                else:
                    item["sentiment"] = "NEUTRAL"

                item["raw_sentiment"] = raw_sent
                item["score"] = res["confidence"]
            else:
                item["sentiment"] = "NEUTRAL"
                item["score"] = 0.5

            item["time"] = item.get("published") or datetime.now().isoformat()

        # Update repository cache
        news_repository.update_news_store(fresh_news)
        return news_repository.get_news(limit=50)


# Global singleton instance of NewsService
news_service = NewsService()

"""
Indian Stock Market News Sentiment Pipeline
=============================================
Fetches news purely from RSS feeds (Economic Times, Moneycontrol, LiveMint,
CNBC-TV18, Reuters/Bloomberg via Google News workaround, etc.), keeps only
articles published in the last RECENCY_MINUTES window, then classifies each
headline as positive/negative/neutral using FinBERT.
"""

import feedparser
import calendar
import json
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
#  RSS FEED SOURCES
# ---------------------------------------------------------------------------

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

    # --- Reuters / Bloomberg workaround ---
    # public one. Google News RSS search is a reliable free substitute: it lets us
    # query "site:reuters.com/bloomberg.com + keyword" and get a real RSS feed back.
    "Reuters (via Google News)": "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com+(markets+OR+RBI+OR+India+OR+Fed)&hl=en-IN&gl=IN&ceid=IN:en",
    "Bloomberg (via Google News)": "https://news.google.com/rss/search?q=when:24h+allinurl:bloomberg.com+(India+OR+markets+OR+Fed+OR+RBI)&hl=en-IN&gl=IN&ceid=IN:en",

    # --- Keyword-based catch-all (fills gaps other feeds miss) ---
    "Google News - Nifty50/Sensex": "https://news.google.com/rss/search?q=when:24h+(Nifty50+OR+Sensex+OR+%22Indian+stock+market%22)&hl=en-IN&gl=IN&ceid=IN:en",
    "Google News - RBI/FII": "https://news.google.com/rss/search?q=when:24h+(RBI+policy+OR+FII+outflow+OR+FII+inflow)&hl=en-IN&gl=IN&ceid=IN:en",
}

# ---------------------------------------------------------------------------
# RECENCY WINDOW
# ---------------------------------------------------------------------------
# Only headlines published within this many minutes of "now" are kept.
# Set to 15 or 30 depending on how fresh you need the signal to be.
RECENCY_MINUTES = 30

# ---------------------------------------------------------------------------
# RSS FETCHING
# ---------------------------------------------------------------------------
def validate_feeds():
    """Quickly checks each RSS URL and reports which ones are working."""
    print("Validating RSS feeds...\n")
    for name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                print(f"  [DEAD]  {name}: {url}")
            else:
                print(f"  [OK]    {name}: {len(feed.entries)} entries")
        except Exception as e:
            print(f"  [ERROR] {name}: {e}")
    print()


def fetch_all_rss():
    """Fetches latest headlines from every RSS feed defined above.
    Stores both the raw published string and a parsed UTC epoch timestamp
    (needed for the recency filter) on each item.
    """
    all_news = []
    for source_name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:40]:  # latest 40 per source
                # feedparser normalizes dates into published_parsed (UTC struct_time)
                # when it can. We use getattr + isinstance instead of .get(...) here
                # because FeedParserDict's .get() is typed loosely (it can technically
                # return nested FeedParserDict/list for other keys), which confuses
                # static type-checkers like Pylance even though it's a non-issue at
                # runtime for this specific key. This form is unambiguous.
                raw_struct = getattr(entry, "published_parsed", None) or \
                             getattr(entry, "updated_parsed", None)
                epoch_utc = (
                    calendar.timegm(raw_struct)
                    if isinstance(raw_struct, time.struct_time)
                    else None
                )

                title = str(entry.get("title", "")).strip()
                link = str(entry.get("link", ""))
                published = str(entry.get("published", entry.get("updated", "")))

                all_news.append({
                    "source": source_name,
                    "title": title,
                    "link": link,
                    "published": published,
                    "published_epoch_utc": epoch_utc,
                })
        except Exception as e:
            print(f"[RSS] Failed to fetch {source_name}: {e}")
    return all_news


def filter_recent_news(news_list, minutes=RECENCY_MINUTES):
    """Keeps only items published within the last `minutes` minutes.
    Items with no parseable timestamp are dropped (we can't confirm they're
    fresh), and this is reported so you know how many were excluded.
    """
    now_utc = datetime.now(timezone.utc).timestamp()
    cutoff = now_utc - (minutes * 60)

    recent, too_old, no_timestamp = [], 0, 0
    for item in news_list:
        epoch = item.get("published_epoch_utc")
        if epoch is None:
            no_timestamp += 1
            continue
        if epoch >= cutoff:
            recent.append(item)
        else:
            too_old += 1

    print(f"Recency filter (last {minutes} min): {len(recent)} kept, "
          f"{too_old} too old, {no_timestamp} had no timestamp (dropped)\n")
    return recent


# ---------------------------------------------------------------------------
# 4. SENTIMENT CLASSIFICATION (FinBERT)
# ---------------------------------------------------------------------------
def load_sentiment_model():
    """Loads FinBERT once — reuse this across all classifications.
    """
    from transformers import pipeline
    print("Loading FinBERT model (first run downloads ~400MB, cached after)...")
    return pipeline(task="text-classification", model="ProsusAI/finbert")


def classify_news(news_list, classifier):
    """
    Runs each headline through FinBERT.
    Returns news_list with sentiment + confidence added to each item.
    FinBERT labels: 'positive', 'negative', 'neutral'.
    We collapse 'neutral' toward whichever side has lower confidence gap,
    but you can keep 3-way output if you prefer — see note below.
    """
    titles = [n["title"] for n in news_list if n["title"]]
    if not titles:
        return news_list

    results = classifier(titles, truncation=True)

    idx = 0
    for item in news_list:
        if not item["title"]:
            continue
        r = results[idx]
        item["sentiment"] = r["label"]        # positive / negative / neutral
        item["confidence"] = round(r["score"], 3)
        idx += 1
    return news_list


# ---------------------------------------------------------------------------
# 5. MAIN PIPELINE
# ---------------------------------------------------------------------------
def run_pipeline(save_to_file=True):
    print(f"=== Pipeline run started: {datetime.now().isoformat()} ===\n")

    # fetch (RSS only)
    combined = fetch_all_rss()
    print(f"Fetched {len(combined)} total headlines from RSS feeds\n")

    if not combined:
        print("No news fetched. Check validate_feeds() output for dead URLs.")
        return []

    # deduplicate by title
    seen_titles = set()
    deduped = []
    for item in combined:
        t = item["title"].lower().strip()
        if t and t not in seen_titles:
            seen_titles.add(t)
            deduped.append(item)
    print(f"After deduplication: {len(deduped)} unique headlines\n")

    # keep only the freshest news (last RECENCY_MINUTES)
    fresh = filter_recent_news(deduped)
    if not fresh:
        print(f"No headlines published in the last {RECENCY_MINUTES} minutes "
              f"right now — this is normal outside market hours or between "
              f"news bursts. Try increasing RECENCY_MINUTES or run again shortly.")
        return []

    # sentiment classification
    classifier = load_sentiment_model()
    classified = classify_news(fresh, classifier)

    # quick summary
    pos = sum(1 for n in classified if n.get("sentiment") == "positive")
    neg = sum(1 for n in classified if n.get("sentiment") == "negative")
    neu = sum(1 for n in classified if n.get("sentiment") == "neutral")
    print(f"Sentiment summary -> Positive: {pos} | Negative: {neg} | Neutral: {neu}\n")

    # save
    if save_to_file:
        fname = f"news_sentiment_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(classified, f, indent=2, ensure_ascii=False)
        print(f"Saved output to {fname}")

    return classified


if __name__ == "__main__":
    # run this once to confirm which RSS URLs actually work on your network
    validate_feeds()

    # Step B: run the full pipeline
    results = run_pipeline()

    # Print sample output — one item per source, so you can see the mix
    print("\n=== Sample (one per source) ===\n")
    seen_sources = set()
    for item in results:
        if item["source"] not in seen_sources:
            seen_sources.add(item["source"])
            print(json.dumps(item, indent=2, ensure_ascii=False))

    # Per-source count, so you can see exactly how much came from where
    print("\n=== Article count per source ===")
    counts = {}
    for item in results:
        counts[item["source"]] = counts.get(item["source"], 0) + 1
    for src, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {src}: {cnt}")
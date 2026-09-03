"""
AI Model Layer - FinBERT Sentiment Classifier
=============================================
Loads the ProsusAI/finbert model via Hugging Face transformers pipeline
and provides headline sentiment classification.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

_sentiment_pipeline = None
_model_failed = False


def load_finbert_model():
    """
    Lazy loads the FinBERT sentiment model pipeline.
    Uses 'text-classification' task with ProsusAI/finbert.
    """
    global _sentiment_pipeline, _model_failed
    if _sentiment_pipeline is not None or _model_failed:
        return _sentiment_pipeline

    try:
        # pyrefly: ignore [missing-import]
        from transformers import pipeline
        logger.info("Loading FinBERT sentiment model (ProsusAI/finbert)...")
        _sentiment_pipeline = pipeline(
            task="text-classification",
            model="ProsusAI/finbert",
            truncation=True
        )
        logger.info("FinBERT model loaded successfully.")
    except Exception as e:
        logger.warning(f"Could not load FinBERT pipeline ({e}). Falling back to heuristic sentiment scoring.")
        _model_failed = True
        _sentiment_pipeline = None

    return _sentiment_pipeline


def classify_headline_fallback(title: str) -> Dict[str, Any]:
    """
    Keyword-based fallback for sentiment if transformer model is offline or downloading.
    """
    title_lower = title.lower()
    bullish_keywords = [
        "surge", "jump", "rally", "gain", "rise", "profit", "bullish", "record high",
        "beat", "growth", "buy", "outperform", "soar", "up", "boost", "climb", "dividend"
    ]
    bearish_keywords = [
        "fall", "drop", "plunge", "slump", "loss", "bearish", "down", "decline",
        "sell", "underperform", "cut", "inflation", "crash", "fear", "crisis", "default"
    ]

    bull_score = sum(1 for w in bullish_keywords if w in title_lower)
    bear_score = sum(1 for w in bearish_keywords if w in title_lower)

    if bull_score > bear_score:
        return {"sentiment": "positive", "confidence": round(0.65 + min(bull_score * 0.1, 0.3), 3)}
    elif bear_score > bull_score:
        return {"sentiment": "negative", "confidence": round(0.65 + min(bear_score * 0.1, 0.3), 3)}
    else:
        return {"sentiment": "neutral", "confidence": 0.70}


def classify_news_titles(titles: List[str]) -> List[Dict[str, Any]]:
    """
    Classifies a list of news headlines.
    Returns list of dicts with 'sentiment' ('positive', 'negative', 'neutral') and 'confidence'.
    """
    if not titles:
        return []

    pipeline_obj = load_finbert_model()

    if pipeline_obj is not None:
        try:
            results = pipeline_obj(titles, truncation=True)
            output = []
            for r in results:
                # FinBERT returns labels: 'positive', 'negative', 'neutral'
                label = r.get("label", "neutral").lower()
                score = round(float(r.get("score", 0.5)), 3)
                output.append({"sentiment": label, "confidence": score})
            return output
        except Exception as e:
            logger.error(f"Error during FinBERT inference: {e}")

    # Fallback if model pipeline is not available
    return [classify_headline_fallback(t) for t in titles]

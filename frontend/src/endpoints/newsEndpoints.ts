/**
 * News API Endpoints definition
 * Targets FastAPI Backend News Sentiment Service
 */
export const NEWS_BASE_URL = import.meta.env.VITE_NEWS_API_URL || 'http://localhost:8000/api/news';

export const NEWS_ENDPOINTS = {
  TOP_NEWS: `${NEWS_BASE_URL}`,
  SENTIMENT_SUMMARY: `${NEWS_BASE_URL}/sentiment-summary`,
  REFRESH_NEWS: `${NEWS_BASE_URL}/refresh`,
};

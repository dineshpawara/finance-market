/**
 * News Service - Business logic for market news & sentiment analysis
 */
import { fetchTopNews, fetchSentimentSummary, triggerNewsRefresh } from '../api/newsApi';
import type { NewsItem } from '../utils/mockMarketData';

export const getMarketNews = async (limit: number = 20): Promise<NewsItem[]> => {
  const news = await fetchTopNews(limit);
  return news.slice(0, limit);
};

export const getMarketSentimentScore = async (): Promise<{ score: number; label: string; count: number; bullish?: number; bearish?: number; neutral?: number }> => {
  const summary = await fetchSentimentSummary();
  return {
    score: summary.score,
    label: summary.label,
    count: summary.count,
    bullish: summary.bullish,
    bearish: summary.bearish,
    neutral: summary.neutral,
  };
};

export const refreshMarketNews = async (): Promise<boolean> => {
  return await triggerNewsRefresh();
};

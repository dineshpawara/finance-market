/**
 * News Controller - React Hook for Managing Real-time News & Sentiment Feed
 */
import { useState, useEffect, useCallback } from 'react';
import type { NewsItem } from '../utils/mockMarketData';
import { getMarketNews, getMarketSentimentScore, refreshMarketNews } from '../services/newsService';

export interface NewsControllerState {
  newsList: NewsItem[];
  filterSentiment: 'ALL' | 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  sentiment: { score: number; label: string; count: number };
  loading: boolean;
  isRefreshing: boolean;
  handleSentimentFilter: (sentiment: 'ALL' | 'BULLISH' | 'BEARISH' | 'NEUTRAL') => void;
  filteredNews: NewsItem[];
  refresh: () => Promise<void>;
}

export const useNewsController = (): NewsControllerState => {
  const [newsList, setNewsList] = useState<NewsItem[]>([]);
  const [filterSentiment, setFilterSentiment] = useState<'ALL' | 'BULLISH' | 'BEARISH' | 'NEUTRAL'>('ALL');
  const [sentiment, setSentiment] = useState<{ score: number; label: string; count: number }>({
    score: 50,
    label: 'NEUTRAL',
    count: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const [news, sent] = await Promise.all([
        getMarketNews(30),
        getMarketSentimentScore(),
      ]);
      setNewsList(news);
      setSentiment(sent);
    } catch (err) {
      console.error('[NewsController] Failed loading news data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshMarketNews();
      await loadData();
    } catch (err) {
      console.error('[NewsController] Failed refreshing feeds:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [loadData]);

  // Initial load and real-time polling every 60 seconds
  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 60000); // Poll every 60s for live news updates

    return () => clearInterval(interval);
  }, [loadData]);

  const filteredNews = newsList.filter(item => {
    if (filterSentiment === 'ALL') return true;
    return item.sentiment === filterSentiment;
  });

  return {
    newsList,
    filterSentiment,
    sentiment,
    loading,
    isRefreshing,
    handleSentimentFilter: setFilterSentiment,
    filteredNews,
    refresh,
  };
};

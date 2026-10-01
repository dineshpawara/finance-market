import { useState, useEffect } from 'react';
import type { CandleData, GlobalMarketItem, NewsItem } from '../utils/mockMarketData';
import { getChartCandles, getGlobalMarketOverview } from '../services/marketService';
import { getMarketNews, getMarketSentimentScore } from '../services/newsService';

export interface DashboardState {
  selectedIndex: string;
  availableIndices: string[];
  candles: CandleData[];
  globalMarkets: GlobalMarketItem[];
  newsItems: NewsItem[];
  sentiment: { score: number; label: string; count: number };
  timeframe: string;
  loading: boolean;
  handleIndexChange: (symbol: string) => void;
  handleTimeframeChange: (tf: string) => void;
  refreshDashboard: () => void;
}

export const useDashboardController = (): DashboardState => {
  const availableIndices = ['NIFTY 50', 'SENSEX', 'BANK NIFTY', 'FIN NIFTY', 'MIDCAP NIFTY'];
  const [selectedIndex, setSelectedIndex] = useState<string>('NIFTY 50');
  const [timeframe, setTimeframe] = useState<string>('1D');
  
  const [candles, setCandles] = useState<CandleData[]>([]);
  const [globalMarkets, setGlobalMarkets] = useState<GlobalMarketItem[]>([]);
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [sentiment, setSentiment] = useState<{ score: number; label: string; count: number }>({ score: 50, label: 'NEUTRAL', count: 0 });
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [candleData, globalData, newsData, sentimentData] = await Promise.all([
        getChartCandles(selectedIndex, timeframe),
        getGlobalMarketOverview(),
        getMarketNews(4),
        getMarketSentimentScore(),
      ]);

      setCandles(candleData);
      setGlobalMarkets(globalData);
      setNewsItems(newsData);
      setSentiment(sentimentData);
    } catch (err) {
      console.error('Failed loading dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedIndex, timeframe]);

  const handleIndexChange = (symbol: string) => {
    setSelectedIndex(symbol);
  };

  const handleTimeframeChange = (tf: string) => {
    setTimeframe(tf);
  };

  return {
    selectedIndex,
    availableIndices,
    candles,
    globalMarkets,
    newsItems,
    sentiment,
    timeframe,
    loading,
    handleIndexChange,
    handleTimeframeChange,
    refreshDashboard: loadData,
  };
};

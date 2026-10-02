/**
 * News API Layer - Connects to FastAPI News Sentiment Backend
 */
import { NEWS_ENDPOINTS } from '../endpoints/newsEndpoints';
import { MOCK_NEWS } from '../utils/mockMarketData';
import type { NewsItem } from '../utils/mockMarketData';

export interface BackendNewsResponseItem {
  id?: string;
  title: string;
  summary?: string;
  source: string;
  published?: string;
  time?: string;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'positive' | 'negative' | 'neutral';
  score?: number;
  confidence?: number;
  link?: string;
  category?: string;
  impactedStocks?: string[];
}

export interface SentimentSummaryResponse {
  score: number;
  label: string;
  count: number;
  bullish?: number;
  bearish?: number;
  neutral?: number;
}

const detectImpactedStocks = (title: string, summary: string): string[] => {
  const text = `${title} ${summary}`.toUpperCase();
  const stocks: string[] = [];

  const stockMap: { [key: string]: string } = {
    ZEE: 'ZEEL',
    ZEEL: 'ZEEL',
    SEBI: 'SEBI',
    NSE: 'NSE',
    RELIANCE: 'RELIANCE',
    JIO: 'JIO',
    TCS: 'TCS',
    INFY: 'INFY',
    INFOSYS: 'INFY',
    HDFC: 'HDFCBANK',
    ICICI: 'ICICIBANK',
    SBI: 'SBIN',
    TATA: 'TATAMOTORS',
    NIFTY: 'NIFTY50',
    SENSEX: 'SENSEX',
    AMAZON: 'AMZN',
    WIPRO: 'WIPRO',
    MARUTI: 'MARUTI',
    MAHINDRA: 'M&M',
    RBI: 'RBI',
    FED: 'FED',
  };

  Object.entries(stockMap).forEach(([keyword, symbol]) => {
    if (text.includes(keyword) && !stocks.includes(symbol)) {
      stocks.push(symbol);
    }
  });

  return stocks.length > 0 ? stocks : ['MARKET'];
};

const normalizeNewsItem = (item: BackendNewsResponseItem, index: number): NewsItem => {
  let sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL' = 'NEUTRAL';
  const rawSent = (item.sentiment || '').toUpperCase();

  if (rawSent === 'BULLISH' || rawSent === 'POSITIVE') {
    sentiment = 'BULLISH';
  } else if (rawSent === 'BEARISH' || rawSent === 'NEGATIVE') {
    sentiment = 'BEARISH';
  }

  const title = item.title || '';
  const summary = item.summary || item.title || '';
  const impacted = item.impactedStocks && item.impactedStocks.length > 0
    ? item.impactedStocks
    : detectImpactedStocks(title, summary);

  return {
    id: item.id || `news-${index}-${Date.now()}`,
    title,
    summary,
    source: item.source || 'Market Feed',
    time: item.published || item.time || new Date().toISOString(),
    sentiment,
    score: item.score || item.confidence || 0.75,
    category: item.category || item.source || 'Stock Market',
    impactedStocks: impacted,
    link: item.link || '#',
  };
};

export const fetchTopNews = async (limit: number = 50): Promise<NewsItem[]> => {
  try {
    const res = await fetch(`${NEWS_ENDPOINTS.TOP_NEWS}?limit=${limit}`);
    if (res.ok) {
      const data: BackendNewsResponseItem[] = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        return data.map(normalizeNewsItem);
      }
    }
  } catch (err) {
    console.warn('[NewsAPI] Backend offline or unreachable.', err);
  }
  return MOCK_NEWS;
};

export const fetchSentimentSummary = async (): Promise<SentimentSummaryResponse> => {
  try {
    const res = await fetch(NEWS_ENDPOINTS.SENTIMENT_SUMMARY);
    if (res.ok) {
      const data: SentimentSummaryResponse = await res.json();
      return data;
    }
  } catch {
    console.warn('[NewsAPI] Sentiment summary backend offline. Using calculated score.');
  }

  // Fallback calculation from MOCK_NEWS if backend unreachable
  const bullish = MOCK_NEWS.filter(n => n.sentiment === 'BULLISH').length;
  const score = Math.round((bullish / MOCK_NEWS.length) * 100);
  return {
    score,
    label: score > 60 ? 'BULLISH' : score < 40 ? 'BEARISH' : 'NEUTRAL',
    count: MOCK_NEWS.length,
    bullish,
    bearish: MOCK_NEWS.filter(n => n.sentiment === 'BEARISH').length,
    neutral: MOCK_NEWS.filter(n => n.sentiment === 'NEUTRAL').length,
  };
};

export const triggerNewsRefresh = async (): Promise<boolean> => {
  try {
    const res = await fetch(NEWS_ENDPOINTS.REFRESH_NEWS, { method: 'POST' });
    return res.ok;
  } catch (err) {
    console.error('[NewsAPI] Failed to trigger news refresh:', err);
    return false;
  }
};


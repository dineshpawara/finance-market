/**
 * Market Data Layer - Connects to FastAPI PostgreSQL / TimescaleDB Market Services
 */
import { generateCandleData, MOCK_GLOBAL_MARKETS, MOCK_NIFTY50_STOCKS, INDEX_BASE_PRICES } from '../utils/mockMarketData';
import type { CandleData, GlobalMarketItem, NiftyStockItem } from '../utils/mockMarketData';

const BASE_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const fetchMarketCandles = async (symbol: string, timeframe: string = '1D'): Promise<CandleData[]> => {
  try {
    const res = await fetch(`${BASE_API_URL}/market/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch {
    // API fallback
  }
  const basePrice = INDEX_BASE_PRICES[symbol] || 1500;
  return generateCandleData(basePrice, 100);
};

export const fetchGlobalMarkets = async (): Promise<GlobalMarketItem[]> => {
  try {
    const res = await fetch(`${BASE_API_URL}/market/global`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch {
    // API fallback
  }
  return MOCK_GLOBAL_MARKETS;
};

export const fetchNifty50Stocks = async (): Promise<NiftyStockItem[]> => {
  try {
    const res = await fetch(`${BASE_API_URL}/market/nifty50`);
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch {
    // API fallback
  }
  return MOCK_NIFTY50_STOCKS;
};

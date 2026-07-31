/**
 * Market API Endpoints definition
 */
export const BASE_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const MARKET_ENDPOINTS = {
  INDICES: `${BASE_API_URL}/market/indices`,
  CANDLES: (symbol: string, timeframe: string = '1D') => 
    `${BASE_API_URL}/market/candles?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}`,
  GLOBAL_MARKETS: `${BASE_API_URL}/market/global`,
  NIFTY50_STOCKS: `${BASE_API_URL}/market/nifty50`,
  STOCK_DETAILS: (symbol: string) => `${BASE_API_URL}/market/stock/${encodeURIComponent(symbol)}`,
};

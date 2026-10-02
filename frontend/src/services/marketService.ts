/**
 * Market Service - Business logic & data transformations for market data
 */
import { fetchGlobalMarkets, fetchMarketCandles, fetchNifty50Stocks } from '../api/marketApi';
import type { CandleData, GlobalMarketItem, NiftyStockItem } from '../utils/mockMarketData';

export const getChartCandles = async (symbol: string, timeframe: string = '1D'): Promise<CandleData[]> => {
  const rawCandles = await fetchMarketCandles(symbol, timeframe);
  // Business logic: ensure candles are sorted by time ascending for TradingView engine
  return rawCandles.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
};

export const getGlobalMarketOverview = async (): Promise<GlobalMarketItem[]> => {
  const items = await fetchGlobalMarkets();
  // Service logic: mark gainers and losers
  return items;
};

export const getNifty50List = async (searchQuery: string = '', sectorFilter: string = 'ALL'): Promise<NiftyStockItem[]> => {
  const stocks = await fetchNifty50Stocks();
  return stocks.filter(stock => {
    const matchesSearch = stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          stock.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = sectorFilter === 'ALL' || stock.sector === sectorFilter;
    return matchesSearch && matchesSector;
  });
};

export const getSectorsList = async (): Promise<string[]> => {
  const stocks = await fetchNifty50Stocks();
  const sectors = Array.from(new Set(stocks.map(s => s.sector)));
  return ['ALL', ...sectors];
};

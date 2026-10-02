import { useState, useEffect } from 'react';
import type { CandleData, NiftyStockItem } from '../utils/mockMarketData';
import { getChartCandles, getNifty50List, getSectorsList } from '../services/marketService';

export interface Nifty50State {
  stocks: NiftyStockItem[];
  sectors: string[];
  searchQuery: string;
  selectedSector: string;
  selectedStock: NiftyStockItem | null;
  stockCandles: CandleData[];
  loading: boolean;
  handleSearchChange: (query: string) => void;
  handleSectorChange: (sector: string) => void;
  handleSelectStock: (stock: NiftyStockItem | null) => void;
}

export const useNifty50Controller = (): Nifty50State => {
  const [stocks, setStocks] = useState<NiftyStockItem[]>([]);
  const [sectors, setSectors] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedSector, setSelectedSector] = useState<string>('ALL');
  const [selectedStock, setSelectedStock] = useState<NiftyStockItem | null>(null);
  const [stockCandles, setStockCandles] = useState<CandleData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchSectors = async () => {
      const sectorData = await getSectorsList();
      setSectors(sectorData);
    };
    fetchSectors();
  }, []);

  useEffect(() => {
    const fetchStocks = async () => {
      setLoading(true);
      const data = await getNifty50List(searchQuery, selectedSector);
      setStocks(data);
      setLoading(false);
    };
    fetchStocks();
  }, [searchQuery, selectedSector]);

  useEffect(() => {
    if (selectedStock) {
      getChartCandles(selectedStock.symbol, '1D').then(setStockCandles);
    } else {
      setStockCandles([]);
    }
  }, [selectedStock]);

  return {
    stocks,
    sectors,
    searchQuery,
    selectedSector,
    selectedStock,
    stockCandles,
    loading,
    handleSearchChange: setSearchQuery,
    handleSectorChange: setSelectedSector,
    handleSelectStock: setSelectedStock,
  };
};

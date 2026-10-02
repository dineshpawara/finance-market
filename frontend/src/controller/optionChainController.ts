import { useState, useEffect } from 'react';
import type { OptionChainSummary } from '../utils/mockMarketData';
import { getOptionChainMatrix } from '../services/optionChainService';

export interface OptionChainState {
  underlying: string;
  availableIndices: string[];
  optionChain: OptionChainSummary | null;
  selectedExpiry: string;
  loading: boolean;
  handleUnderlyingChange: (symbol: string) => void;
  handleExpiryChange: (expiry: string) => void;
  refreshOptionChain: () => void;
}

export const useOptionChainController = (): OptionChainState => {
  const availableIndices = ['NIFTY 50', 'BANK NIFTY', 'FIN NIFTY'];
  const [underlying, setUnderlying] = useState<string>('NIFTY 50');
  const [optionChain, setOptionChain] = useState<OptionChainSummary | null>(null);
  const [selectedExpiry, setSelectedExpiry] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const chain = await getOptionChainMatrix(underlying, selectedExpiry);
      setOptionChain(chain);
      if (!selectedExpiry && chain.expiryDates.length > 0) {
        setSelectedExpiry(chain.selectedExpiry || chain.expiryDates[0]);
      }
    } catch (err) {
      console.error('Failed loading Option Chain', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [underlying, selectedExpiry]);

  return {
    underlying,
    availableIndices,
    optionChain,
    selectedExpiry,
    loading,
    handleUnderlyingChange: (symbol: string) => {
      setUnderlying(symbol);
      setSelectedExpiry('');
    },
    handleExpiryChange: setSelectedExpiry,
    refreshOptionChain: loadData,
  };
};

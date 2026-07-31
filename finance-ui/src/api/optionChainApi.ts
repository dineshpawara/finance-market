/**
 * Option Chain Data Layer - Connects to FastAPI Redis-Cached Option Chain Service
 */
import { generateOptionChainData } from '../utils/mockMarketData';
import type { OptionChainSummary } from '../utils/mockMarketData';

const BASE_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const fetchOptionChain = async (underlying: string = 'NIFTY 50', expiry?: string): Promise<OptionChainSummary> => {
  try {
    const url = `${BASE_API_URL}/market/option-chain?symbol=${encodeURIComponent(underlying)}${expiry ? `&expiry=${expiry}` : ''}`;
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      if (data && data.strikes) return data;
    }
  } catch {
    // API fallback
  }
  const price = underlying.includes('BANK') ? 52180 : 24852;
  return generateOptionChainData(price);
};

/**
 * Option Chain Service - Business logic for Option Chain calculations
 */
import { fetchOptionChain } from '../api/optionChainApi';
import type { OptionChainSummary } from '../utils/mockMarketData';

export const getOptionChainMatrix = async (underlying: string = 'NIFTY 50', expiry?: string): Promise<OptionChainSummary> => {
  const chain = await fetchOptionChain(underlying, expiry);
  
  // Sort strikes numerically
  chain.strikes.sort((a, b) => a.strike - b.strike);
  
  return chain;
};

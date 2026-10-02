/**
 * Option Chain API Endpoints definition
 */
import { BASE_API_URL } from './marketEndpoints';

export const OPTION_CHAIN_ENDPOINTS = {
  GET_CHAIN: (underlying: string, expiry?: string) => 
    `${BASE_API_URL}/option-chain?symbol=${encodeURIComponent(underlying)}${expiry ? `&expiry=${expiry}` : ''}`,
  EXPIRIES: (underlying: string) => 
    `${BASE_API_URL}/option-chain/expiries?symbol=${encodeURIComponent(underlying)}`,
};

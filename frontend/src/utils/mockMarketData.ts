export interface CandleData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface GlobalMarketItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  region: string;
  flag: string;
}

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  time: string;
  sentiment: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  score: number;
  category: string;
  impactedStocks: string[];
  link?: string;
}

export interface NiftyStockItem {
  symbol: string;
  name: string;
  sector: string;
  price: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  high52: number;
  low52: number;
  volume: number;
  marketCapCr: number;
  pe: number;
}

export interface OptionStrikeData {
  strike: number;
  callOI: number;
  callChgOI: number;
  callLtp: number;
  callIv: number;
  putLtp: number;
  putIv: number;
  putChgOI: number;
  putOI: number;
}

export interface OptionChainSummary {
  underlying: string;
  underlyingPrice: number;
  expiryDates: string[];
  selectedExpiry: string;
  pcr: number;
  maxPain: number;
  totalCallOI: number;
  totalPutOI: number;
  strikes: OptionStrikeData[];
}

/**
 * Generate historical candlestick OHLC data for Lightweight Charts
 */
export const generateCandleData = (basePrice: number = 24850, count: number = 120): CandleData[] => {
  const candles: CandleData[] = [];
  const now = new Date();
  let currentPrice = basePrice;
  const daysInMs = 24 * 60 * 60 * 1000;

  for (let i = count; i >= 0; i--) {
    const d = new Date(now.getTime() - i * daysInMs);
    // Skip weekends
    if (d.getDay() === 0 || d.getDay() === 6) continue;

    const dateStr = d.toISOString().split('T')[0];
    const volatility = currentPrice * 0.008;
    const change = (Math.random() - 0.48) * volatility;
    
    const open = currentPrice;
    const close = Number((open + change).toFixed(2));
    const high = Number((Math.max(open, close) + Math.random() * volatility * 0.5).toFixed(2));
    const low = Number((Math.min(open, close) - Math.random() * volatility * 0.5).toFixed(2));
    const volume = Math.floor(Math.random() * 500000) + 100000;

    candles.push({ time: dateStr, open, high, low, close, volume });
    currentPrice = close;
  }
  return candles;
};

/**
 * Multi-day & Intraday Timeframe Candle Generator for TradingView lightweight charts
 */
export const generateTimeframeCandles = (
  symbol: string = 'NIFTY 50',
  timeframe: string = '5m',
  basePriceInput?: number
): CandleData[] => {
  let basePrice = basePriceInput || INDEX_BASE_PRICES[symbol] || 24852.15;
  if (symbol.includes('SENSEX')) basePrice = 81450.80;
  else if (symbol.includes('BANK')) basePrice = 52180.40;
  else if (symbol.includes('RELIANCE')) basePrice = 2984.50;
  else if (symbol.includes('TCS')) basePrice = 4210.80;
  else if (symbol.includes('HDFC')) basePrice = 1642.15;
  else if (symbol.includes('INFY')) basePrice = 1785.40;

  let intervalSeconds = 300; // default 5m
  let count = 150;
  let isDaily = false;

  if (timeframe === '1m') { intervalSeconds = 60; count = 180; }
  else if (timeframe === '3m') { intervalSeconds = 180; count = 150; }
  else if (timeframe === '5m') { intervalSeconds = 300; count = 150; }
  else if (timeframe === '15m') { intervalSeconds = 900; count = 120; }
  else if (timeframe === '1h') { intervalSeconds = 3600; count = 120; }
  else if (timeframe === '1D') { intervalSeconds = 86400; count = 180; isDaily = true; }

  const candles: CandleData[] = [];
  const now = new Date();

  if (isDaily) {
    let currentPrice = basePrice * 0.92;
    const daysInMs = 24 * 60 * 60 * 1000;
    for (let i = count; i >= 0; i--) {
      const d = new Date(now.getTime() - i * daysInMs);
      if (d.getDay() === 0 || d.getDay() === 6) continue;
      const dateStr = d.toISOString().split('T')[0];
      const volatility = currentPrice * 0.012;
      const wave = Math.sin(i / 12) * (volatility * 0.7);
      const change = (Math.random() - 0.485) * volatility + wave;

      const open = Number(currentPrice.toFixed(2));
      const close = Number(Math.max(10, open + change).toFixed(2));
      const high = Number((Math.max(open, close) + Math.random() * volatility * 0.5).toFixed(2));
      const low = Number((Math.min(open, close) - Math.random() * volatility * 0.5).toFixed(2));
      const volume = Math.floor(Math.random() * 2000000) + 500000;

      candles.push({ time: dateStr, open, high, low, close, volume });
      currentPrice = close;
    }
  } else {
    const nowSec = Math.floor(now.getTime() / 1000);
    const currentIntervalSec = Math.floor(nowSec / intervalSeconds) * intervalSeconds;
    let currentPrice = basePrice * 0.985;

    for (let i = count; i >= 0; i--) {
      const timeSec = currentIntervalSec - (i * intervalSeconds);
      const volatility = currentPrice * (timeframe === '1h' ? 0.005 : 0.002);
      const wave = Math.sin(i / 8) * (volatility * 0.5);
      const change = (Math.random() - 0.49) * volatility + wave;

      const open = Number(currentPrice.toFixed(2));
      const close = Number(Math.max(10, open + change).toFixed(2));
      const high = Number((Math.max(open, close) + Math.random() * volatility * 0.5).toFixed(2));
      const low = Number((Math.min(open, close) - Math.random() * volatility * 0.5).toFixed(2));
      const volume = Math.floor(Math.random() * 80000) + 12000;

      candles.push({ time: String(timeSec), open, high, low, close, volume });
      currentPrice = close;
    }
  }

  return candles;
};

export const INDEX_BASE_PRICES: Record<string, number> = {
  'NIFTY 50': 24852.15,
  'SENSEX': 81450.80,
  'BANK NIFTY': 52180.40,
  'FIN NIFTY': 23410.25,
  'MIDCAP NIFTY': 12940.60,
};

export const MOCK_GLOBAL_MARKETS: GlobalMarketItem[] = [
  { symbol: 'GIFT_NIFTY', name: 'GIFT Nifty', price: 24915.0, change: 62.8, changePercent: 0.25, region: 'Asia/India', flag: '🇮🇳' },
  { symbol: 'SP500', name: 'S&P 500', price: 5542.2, change: 18.4, changePercent: 0.33, region: 'US', flag: '🇺🇸' },
  { symbol: 'NASDAQ', name: 'Nasdaq 100', price: 19820.5, change: 145.2, changePercent: 0.74, region: 'US', flag: '🇺🇸' },
  { symbol: 'FTSE100', name: 'FTSE 100', price: 8210.4, change: -12.3, changePercent: -0.15, region: 'Europe', flag: '🇬🇧' },
  { symbol: 'NIKKEI', name: 'Nikkei 225', price: 38450.0, change: 310.5, changePercent: 0.81, region: 'Asia', flag: '🇯🇵' },
  { symbol: 'BRENT_CRUDE', name: 'Brent Crude', price: 79.45, change: -0.85, changePercent: -1.06, region: 'Commodity', flag: '🛢️' },
  { symbol: 'GOLD', name: 'Gold (Oz)', price: 2415.80, change: 14.2, changePercent: 0.59, region: 'Commodity', flag: '🥇' },
];

export const MOCK_NEWS: NewsItem[] = [
  {
    id: 'n1',
    title: 'RBI Monetary Policy: Repo Rate Kept Unchanged at 6.5%, Stance Remains Focused on Withdrawal of Accommodation',
    summary: 'The Monetary Policy Committee decided to maintain status quo on key interest rates while highlighting resilient GDP growth forecasts.',
    source: 'Moneycontrol',
    time: new Date(Date.now() - 15 * 60000).toISOString(),
    sentiment: 'BULLISH',
    score: 0.78,
    category: 'Economy',
    impactedStocks: ['HDFCBANK', 'ICICIBANK', 'SBIN'],
  },
  {
    id: 'n2',
    title: 'Reliance Industries Reports Q1 Net Profit Surge of 12% Driven by Retail & Digital Services Expansion',
    summary: 'Jio Platforms and Reliance Retail deliver record EBITDA, offsetting margin pressure in the Oil-to-Chemicals business segment.',
    source: 'Economic Times',
    time: new Date(Date.now() - 45 * 60000).toISOString(),
    sentiment: 'BULLISH',
    score: 0.85,
    category: 'Earnings',
    impactedStocks: ['RELIANCE'],
  },
  {
    id: 'n3',
    title: 'IT Sector Q1 Review: TCS & Infosys Lead Deal Wins Despite Broader Discretionary Tech Spending Slowdown',
    summary: 'Tier-1 IT major order books remain strong driven by Cloud transformation and GenAI proof of concepts.',
    source: 'LiveMint',
    time: new Date(Date.now() - 120 * 60000).toISOString(),
    sentiment: 'NEUTRAL',
    score: 0.52,
    category: 'IT Sector',
    impactedStocks: ['TCS', 'INFY', 'WIPRO', 'HCLTECH'],
  },
  {
    id: 'n4',
    title: 'Foreign Institutional Investors (FIIs) Net Buyers of ₹3,420 Crore in Indian Equities Today',
    summary: 'Domestic funds (DIIs) also matched with net purchases of ₹1,850 Crore as market sentiment turns favorable.',
    source: 'NSE India',
    time: new Date(Date.now() - 180 * 60000).toISOString(),
    sentiment: 'BULLISH',
    score: 0.91,
    category: 'Institutional Flows',
    impactedStocks: ['NIFTY50', 'BANKNIFTY'],
  },
  {
    id: 'n5',
    title: 'Auto Sales July: Tata Motors & Mahindra Report 18% YoY Growth in SUV Deliveries',
    summary: 'Passenger vehicle retail demand surges ahead of festive season; EV adoption crosses milestone monthly run rate.',
    source: 'Financial Express',
    time: new Date(Date.now() - 300 * 60000).toISOString(),
    sentiment: 'BULLISH',
    score: 0.74,
    category: 'Automobile',
    impactedStocks: ['TATAMOTORS', 'M&M', 'MARUTI'],
  },
];

export const MOCK_NIFTY50_STOCKS: NiftyStockItem[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd.', sector: 'Energy & Retail', price: 2984.50, change: 35.20, changePercent: 1.19, high: 2998.00, low: 2950.10, high52: 3217.90, low52: 2220.30, volume: 4820150, marketCapCr: 2018500, pe: 28.4 },
  { symbol: 'TCS', name: 'Tata Consultancy Services', sector: 'Information Tech', price: 4210.80, change: -18.40, changePercent: -0.44, high: 4250.00, low: 4190.20, high52: 4585.00, low52: 3315.00, volume: 1950420, marketCapCr: 1524100, pe: 31.8 },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd.', sector: 'Banking & Financials', price: 1642.15, change: 14.80, changePercent: 0.91, high: 1655.00, low: 1628.00, high52: 1794.00, low52: 1363.55, volume: 8940120, marketCapCr: 1250800, pe: 18.6 },
  { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd.', sector: 'Banking & Financials', price: 1215.30, change: 11.20, changePercent: 0.93, high: 1224.00, low: 1201.50, high52: 1258.00, low52: 898.00, volume: 6410200, marketCapCr: 854200, pe: 17.2 },
  { symbol: 'INFY', name: 'Infosys Limited', sector: 'Information Tech', price: 1785.40, change: 22.10, changePercent: 1.25, high: 1795.00, low: 1760.00, high52: 1978.00, low52: 1355.00, volume: 5120800, marketCapCr: 741200, pe: 29.1 },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd.', sector: 'Telecom', price: 1520.60, change: 18.50, changePercent: 1.23, high: 1535.00, low: 1498.00, high52: 1610.00, low52: 860.00, volume: 3850100, marketCapCr: 902100, pe: 42.5 },
  { symbol: 'ITC', name: 'ITC Limited', sector: 'FMCG', price: 495.20, change: 2.80, changePercent: 0.57, high: 498.50, low: 491.00, high52: 528.00, low52: 399.00, volume: 4120800, marketCapCr: 618500, pe: 28.9 },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking & Financials', price: 848.75, change: -4.25, changePercent: -0.50, high: 859.00, low: 842.10, high52: 912.00, low52: 560.00, volume: 7850400, marketCapCr: 757400, pe: 11.4 },
  { symbol: 'LT', name: 'Larsen & Toubro Ltd.', sector: 'Infrastructure', price: 3680.10, change: 48.60, changePercent: 1.34, high: 3710.00, low: 3625.00, high52: 3919.90, low52: 2820.00, volume: 1820400, marketCapCr: 506200, pe: 34.2 },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd.', sector: 'FMCG', price: 2685.00, change: -12.50, changePercent: -0.46, high: 2710.00, low: 2672.00, high52: 2840.00, low52: 2172.00, volume: 1420100, marketCapCr: 630800, pe: 58.6 },
  { symbol: 'AXISBANK', name: 'Axis Bank Ltd.', sector: 'Banking & Financials', price: 1165.40, change: 8.90, changePercent: 0.77, high: 1178.00, low: 1152.00, high52: 1339.00, low52: 930.00, volume: 4210000, marketCapCr: 359400, pe: 13.8 },
  { symbol: 'M&M', name: 'Mahindra & Mahindra Ltd.', sector: 'Automobile', price: 2915.20, change: 65.40, changePercent: 2.30, high: 2940.00, low: 2850.00, high52: 3015.00, low52: 1440.00, volume: 2980100, marketCapCr: 362500, pe: 30.5 },
  { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd.', sector: 'Automobile', price: 1045.80, change: 18.20, changePercent: 1.77, high: 1058.00, low: 1024.00, high52: 1179.00, low52: 608.00, volume: 6240800, marketCapCr: 347800, pe: 11.2 },
  { symbol: 'NTPC', name: 'NTPC Limited', sector: 'Power & Utilities', price: 412.50, change: 5.80, changePercent: 1.43, high: 418.00, low: 405.00, high52: 448.00, low52: 210.00, volume: 9120400, marketCapCr: 400100, pe: 19.4 },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical Ind.', sector: 'Healthcare', price: 1740.25, change: -8.10, changePercent: -0.46, high: 1762.00, low: 1730.00, high52: 1820.00, low52: 1110.00, volume: 1540200, marketCapCr: 417500, pe: 41.2 },
];

export const generateOptionChainData = (underlyingPrice: number = 24852): OptionChainSummary => {
  const strikeInterval = 50;
  const atmStrike = Math.round(underlyingPrice / strikeInterval) * strikeInterval;
  const strikes: OptionStrikeData[] = [];
  
  let totalCallOI = 0;
  let totalPutOI = 0;

  for (let i = -10; i <= 10; i++) {
    const strike = atmStrike + i * strikeInterval;
    const isCallITM = strike < atmStrike;
    const isPutITM = strike > atmStrike;
    const diff = Math.abs(strike - atmStrike);

    // Call metrics
    const callLtp = isCallITM ? Number((underlyingPrice - strike + Math.random() * 20 + 40).toFixed(2)) : Number((Math.max(10, 250 - diff * 0.8 + Math.random() * 15)).toFixed(2));
    const callOI = Math.floor((Math.max(50, 2500 - diff * 5) + Math.random() * 800) * 10);
    const callChgOI = Math.floor((Math.random() - 0.4) * 800);
    const callIv = Number((12.5 + Math.random() * 3).toFixed(1));

    // Put metrics
    const putLtp = isPutITM ? Number((strike - underlyingPrice + Math.random() * 20 + 40).toFixed(2)) : Number((Math.max(10, 250 - diff * 0.8 + Math.random() * 15)).toFixed(2));
    const putOI = Math.floor((Math.max(50, 2500 - diff * 5) + Math.random() * 800) * 10);
    const putChgOI = Math.floor((Math.random() - 0.35) * 800);
    const putIv = Number((13.1 + Math.random() * 3).toFixed(1));

    totalCallOI += callOI;
    totalPutOI += putOI;

    strikes.push({
      strike,
      callOI,
      callChgOI,
      callLtp,
      callIv,
      putLtp,
      putIv,
      putChgOI,
      putOI,
    });
  }

  const pcr = Number((totalPutOI / (totalCallOI || 1)).toFixed(2));
  const maxPain = atmStrike;

  return {
    underlying: 'NIFTY 50',
    underlyingPrice,
    expiryDates: ['31-JUL-2026', '07-AUG-2026', '14-AUG-2026', '28-AUG-2026'],
    selectedExpiry: '31-JUL-2026',
    pcr,
    maxPain,
    totalCallOI,
    totalPutOI,
    strikes,
  };
};

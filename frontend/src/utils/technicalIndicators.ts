import type { CandleData } from './mockMarketData';

export interface LinePoint {
  time: string;
  value: number;
}

export interface BollingerBandPoint {
  time: string;
  upper: number;
  middle: number;
  lower: number;
}

export interface MacdPoint {
  time: string;
  macd: number;
  signal: number;
  histogram: number;
}

/**
 * Simple Moving Average (SMA)
 */
export function calculateSMA(data: CandleData[], period: number = 20): LinePoint[] {
  const result: LinePoint[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;
    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    result.push({
      time: data[i].time,
      value: Number((sum / period).toFixed(2)),
    });
  }
  return result;
}

/**
 * Exponential Moving Average (EMA)
 */
export function calculateEMA(data: CandleData[], period: number = 50): LinePoint[] {
  const result: LinePoint[] = [];
  if (data.length < period) return result;

  const multiplier = 2 / (period + 1);
  let prevEma = 0;
  for (let i = 0; i < period; i++) {
    prevEma += data[i].close;
  }
  prevEma /= period;
  result.push({ time: data[period - 1].time, value: Number(prevEma.toFixed(2)) });

  for (let i = period; i < data.length; i++) {
    const currentClose = data[i].close;
    const currentEma = (currentClose - prevEma) * multiplier + prevEma;
    result.push({
      time: data[i].time,
      value: Number(currentEma.toFixed(2)),
    });
    prevEma = currentEma;
  }
  return result;
}

/**
 * Volume Weighted Average Price (VWAP)
 */
export function calculateVWAP(data: CandleData[]): LinePoint[] {
  const result: LinePoint[] = [];
  let cumulativeTPV = 0; // Typical Price * Volume
  let cumulativeVol = 0;

  for (let i = 0; i < data.length; i++) {
    const candle = data[i];
    const typicalPrice = (candle.high + candle.low + candle.close) / 3;
    const volume = candle.volume || 1;
    cumulativeTPV += typicalPrice * volume;
    cumulativeVol += volume;

    const vwap = cumulativeTPV / cumulativeVol;
    result.push({
      time: candle.time,
      value: Number(vwap.toFixed(2)),
    });
  }
  return result;
}

/**
 * Bollinger Bands (Upper, Middle, Lower)
 */
export function calculateBollingerBands(
  data: CandleData[],
  period: number = 20,
  stdDevMultiplier: number = 2
): BollingerBandPoint[] {
  const result: BollingerBandPoint[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;

    let sum = 0;
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close;
    }
    const sma = sum / period;

    let varianceSum = 0;
    for (let j = 0; j < period; j++) {
      varianceSum += Math.pow(data[i - j].close - sma, 2);
    }
    const stdDev = Math.sqrt(varianceSum / period);

    result.push({
      time: data[i].time,
      middle: Number(sma.toFixed(2)),
      upper: Number((sma + stdDevMultiplier * stdDev).toFixed(2)),
      lower: Number((sma - stdDevMultiplier * stdDev).toFixed(2)),
    });
  }
  return result;
}

/**
 * Relative Strength Index (RSI)
 */
export function calculateRSI(data: CandleData[], period: number = 14): LinePoint[] {
  const result: LinePoint[] = [];
  if (data.length <= period) return result;

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const diff = data[i].close - data[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses += Math.abs(diff);
  }

  let avgGain = gains / period;
  let avgLoss = losses / period;

  let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
  let rsi = 100 - 100 / (1 + rs);
  result.push({ time: data[period].time, value: Number(rsi.toFixed(2)) });

  for (let i = period + 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close;
    const currentGain = diff >= 0 ? diff : 0;
    const currentLoss = diff < 0 ? Math.abs(diff) : 0;

    avgGain = (avgGain * (period - 1) + currentGain) / period;
    avgLoss = (avgLoss * (period - 1) + currentLoss) / period;

    rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    rsi = 100 - 100 / (1 + rs);
    result.push({ time: data[i].time, value: Number(rsi.toFixed(2)) });
  }

  return result;
}

/**
 * MACD (Moving Average Convergence Divergence)
 */
export function calculateMACD(
  data: CandleData[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): MacdPoint[] {
  const result: MacdPoint[] = [];
  const fastEma = calculateEMA(data, fastPeriod);
  const slowEma = calculateEMA(data, slowPeriod);

  // Map by time
  const slowEmaMap = new Map(slowEma.map(item => [item.time, item.value]));
  const rawMacdLines: LinePoint[] = [];

  fastEma.forEach(fast => {
    const slowVal = slowEmaMap.get(fast.time);
    if (slowVal !== undefined) {
      rawMacdLines.push({
        time: fast.time,
        value: Number((fast.value - slowVal).toFixed(2)),
      });
    }
  });

  if (rawMacdLines.length < signalPeriod) return result;

  // Calculate signal line (EMA of MACD line)
  const multiplier = 2 / (signalPeriod + 1);
  let prevSignal = 0;
  for (let i = 0; i < signalPeriod; i++) {
    prevSignal += rawMacdLines[i].value;
  }
  prevSignal /= signalPeriod;

  for (let i = signalPeriod - 1; i < rawMacdLines.length; i++) {
    const currentMacd = rawMacdLines[i].value;
    const currentSignal = i === signalPeriod - 1 ? prevSignal : (currentMacd - prevSignal) * multiplier + prevSignal;
    prevSignal = currentSignal;

    const hist = currentMacd - currentSignal;
    result.push({
      time: rawMacdLines[i].time,
      macd: Number(currentMacd.toFixed(2)),
      signal: Number(currentSignal.toFixed(2)),
      histogram: Number(hist.toFixed(2)),
    });
  }

  return result;
}

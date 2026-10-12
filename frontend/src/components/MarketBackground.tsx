import React, { useMemo } from 'react';
import { useTheme } from '../context/ThemeContext';

export const MarketBackground: React.FC = () => {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Generate realistic candlestick data with wicks and bodies
  const candlesticks = useMemo(() => {
    const list = [];
    let currentClose = 180;
    for (let i = 0; i < 38; i++) {
      const isBullish = (i * 7 + 13) % 3 !== 0; // Natural-looking bullish/bearish distribution
      const change = Math.sin(i * 0.45) * 22 + ((i % 5) - 2) * 8;
      const open = Math.max(80, Math.min(260, currentClose + (isBullish ? -12 : 12)));
      const close = Math.max(70, Math.min(270, open + (isBullish ? Math.abs(change) + 14 : -(Math.abs(change) + 12))));
      const high = Math.max(open, close) + 8 + (i % 4) * 4;
      const low = Math.min(open, close) - 8 - ((i + 2) % 4) * 4;
      currentClose = close;

      list.push({
        id: i,
        x: i * 36 + 20,
        open,
        close,
        high,
        low,
        isBullish,
      });
    }
    return list;
  }, []);

  // Floating financial badges/tickers in the background
  const floatingTags = [
    { label: '▲ NIFTY 24,852.15 (+0.72%)', top: '14%', left: '8%' },
    { label: '₹ PROFIT TARGET: REACHED', top: '22%', right: '12%' },
    { label: '▲ BANKNIFTY 52,140.35 (+1.14%)', bottom: '26%', left: '10%' },
    { label: '$ S&P 500: BULLISH MOMENTUM', bottom: '16%', right: '14%' },
    { label: 'VOLUME SPIKE: 2.4M', top: '78%', left: '42%' },
  ];

  const floatingCurrencies = [
    { symbol: '$', top: '10%', left: '26%', size: '36px', opacity: 0.12 },
    { symbol: '₹', top: '28%', left: '78%', size: '44px', opacity: 0.15 },
    { symbol: '$', bottom: '22%', left: '22%', size: '40px', opacity: 0.1 },
    { symbol: '₹', bottom: '12%', right: '28%', size: '48px', opacity: 0.14 },
    { symbol: '%', top: '55%', left: '6%', size: '32px', opacity: 0.08 },
    { symbol: '▲', top: '42%', right: '6%', size: '34px', opacity: 0.12 },
  ];

  const greenColor = isDark ? '#00d09c' : '#00a87d';
  const redColor = isDark ? '#eb5757' : '#df2020';
  const gridLineColor = isDark ? '#252932' : '#e2e8f0';

  return (
    <div className="market-bg-container">
      {/* Dynamic ambient radial gradients */}
      <div className="market-bg-glow market-bg-glow-green" />
      <div className="market-bg-glow market-bg-glow-blue" />

      {/* Grid Pattern */}
      <div className="market-bg-grid" />

      {/* Realistic Candlestick Chart SVG Stream */}
      <div className="market-bg-chart-wrapper">
        <svg
          viewBox="0 0 1400 320"
          preserveAspectRatio="none"
          className="market-bg-svg"
        >
          {/* Subtle grid lines in chart */}
          <line x1="0" y1="80" x2="1400" y2="80" stroke={gridLineColor} strokeDasharray="4 4" strokeWidth="1" />
          <line x1="0" y1="160" x2="1400" y2="160" stroke={gridLineColor} strokeDasharray="4 4" strokeWidth="1" />
          <line x1="0" y1="240" x2="1400" y2="240" stroke={gridLineColor} strokeDasharray="4 4" strokeWidth="1" />

          {/* Render individual candlesticks */}
          {candlesticks.map((candle) => {
            const candleColor = candle.isBullish ? greenColor : redColor;
            const topY = Math.min(candle.open, candle.close);
            const height = Math.max(4, Math.abs(candle.close - candle.open));

            return (
              <g key={candle.id}>
                {/* Candle Upper and Lower Wick */}
                <line
                  x1={candle.x + 8}
                  y1={candle.high}
                  x2={candle.x + 8}
                  y2={candle.low}
                  stroke={candleColor}
                  strokeWidth="1.8"
                  opacity="0.85"
                />
                {/* Candle Body */}
                <rect
                  x={candle.x}
                  y={topY}
                  width="16"
                  height={height}
                  rx="2"
                  fill={candleColor}
                  fillOpacity={candle.isBullish ? '0.85' : '0.75'}
                  stroke={candleColor}
                  strokeWidth="1"
                />
              </g>
            );
          })}

          {/* Glowing Exponential Trendline across the candlesticks */}
          <path
            d="M 20 220 Q 240 180, 480 200 T 820 140 T 1150 110 T 1400 90"
            fill="none"
            stroke={greenColor}
            strokeWidth="2.5"
            strokeDasharray="6 3"
            opacity="0.6"
          />
        </svg>
      </div>

      {/* Floating Currency symbols */}
      {floatingCurrencies.map((item, idx) => (
        <div
          key={idx}
          className="market-bg-currency-symbol"
          style={{
            top: item.top,
            bottom: item.bottom,
            left: item.left,
            right: item.right,
            fontSize: item.size,
            opacity: item.opacity,
          }}
        >
          {item.symbol}
        </div>
      ))}

      {/* Floating market status chips */}
      {floatingTags.map((tag, idx) => (
        <div
          key={idx}
          className="market-bg-ticker-tag"
          style={{
            top: tag.top,
            bottom: tag.bottom,
            left: tag.left,
            right: tag.right,
          }}
        >
          {tag.label}
        </div>
      ))}
    </div>
  );
};

export default MarketBackground;

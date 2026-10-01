import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  SlidersHorizontal,
  X,
  Trash2,
  MousePointer,
  MinusSquare,
  Type,
  Ruler,
  BarChart2,
  Layers,
  History,
  Briefcase,
  Wallet,
  ArrowUpRight,
  ArrowDownRight,
  Check,
  ChevronDown,
  GripVertical
} from 'lucide-react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries, LineSeries } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import { GROWW_THEME, getChartThemeOptions } from '../utils/theme';
import { useTheme } from '../context/ThemeContext';
import { usePaperTrading } from '../context/PaperTradingContext';
import { generateTimeframeCandles, generateOptionChainData } from '../utils/mockMarketData';
import type { CandleData, OptionStrikeData } from '../utils/mockMarketData';
import {
  calculateSMA,
  calculateEMA,
  calculateVWAP,
  calculateBollingerBands
} from '../utils/technicalIndicators';

interface ProTradingTerminalProps {
  symbol?: string;
  onClose?: () => void;
}

export type DockTab = 'chain' | 'positions' | 'orders' | 'depth' | 'watchlist' | 'balance';

export const ProTradingTerminal: React.FC<ProTradingTerminalProps> = ({
  symbol: initialSymbol = 'NIFTY 50',
  onClose,
}) => {
  const { theme } = useTheme();
  const { balance, availableMargin, usedMargin, totalPnl, positions, orders, placeOrder, closePosition, resetAccount } = usePaperTrading();

  // Active Symbol, Timeframe & Time Range State
  const [activeSymbol, setActiveSymbol] = useState(initialSymbol);
  const [timeframe, setTimeframe] = useState('5m');
  const [activeTimeRange, setActiveTimeRange] = useState('1D');
  const [activeDockTab, setActiveDockTab] = useState<DockTab | null>('chain');

  // Indicators Toggle State
  const [showIndicatorModal, setShowIndicatorModal] = useState(false);
  const [indicators, setIndicators] = useState({
    sma: true,
    ema: true,
    vwap: false,
    bollinger: false,
    rsi: false,
    macd: false,
  });

  // Paper Trading Quick Order Form State
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderSide, setOrderSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderQty, setOrderQty] = useState(50); // Default Nifty lot size
  const [orderPrice, setOrderPrice] = useState(24366.70);

  // Drawing Tools State
  const [activeDrawingTool, setActiveDrawingTool] = useState<string>('cursor');

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartApiRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);

  // Multi-day / Multi-timeframe Candles State
  const [candles, setCandles] = useState<CandleData[]>(() => generateTimeframeCandles(initialSymbol, '5m'));
  const [optionChainData] = useState(() => generateOptionChainData(24350));
  const optionChain: OptionStrikeData[] = optionChainData.strikes;

  // Current Live Price
  const currentCandle = candles[candles.length - 1];
  const livePrice = currentCandle ? currentCandle.close : 24366.70;
  const priceChange = currentCandle ? currentCandle.close - candles[0].close : 66.45;
  const priceChangePercent = ((priceChange / (livePrice - priceChange)) * 100).toFixed(2);

  // Header Quick Tickers
  const headerTickers = [
    { name: 'NIFTY', price: '24,383.60', change: '+66.45 (+0.27%)', positive: true },
    { name: 'SENSEX', price: '78,094.64', change: '+166.49 (+0.21%)', positive: true },
    { name: 'Crude Oil 19 Aug Fut', price: '₹8,162.00', change: '+125.00 (+1.56%)', positive: true },
    { name: 'Natural Gas 28 Jul Fut', price: '₹255.00', change: '-1.80 (-0.70%)', positive: false },
    { name: 'BANKNIFTY', price: '57,264.85', change: '+117.35 (+0.21%)', positive: true },
  ];

  // Initialize & Create Main Lightweight Chart (Runs on symbol, timeframe, indicators or theme change)
  useEffect(() => {
    if (!chartContainerRef.current) return;

    if (chartApiRef.current) {
      try {
        chartApiRef.current.remove();
      } catch {
        // Safe catch if already disposed
      }
      chartApiRef.current = null;
    }

    const themeOpts = getChartThemeOptions(theme);
    const initialCandles = generateTimeframeCandles(activeSymbol, timeframe);
    setCandles(initialCandles);

    // Create Main Chart with full free-moving pan, zoom & drag controls
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 480,
      layout: {
        background: { type: ColorType.Solid, color: themeOpts.layout.background.color },
        textColor: themeOpts.layout.textColor,
        fontFamily: 'Inter, sans-serif',
      },
      grid: themeOpts.grid,
      crosshair: themeOpts.crosshair,
      timeScale: {
        borderColor: themeOpts.timeScale.borderColor,
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12,
        barSpacing: 8,
        minBarSpacing: 1,
        fixLeftEdge: false,
        fixRightEdge: false,
        lockVisibleTimeRangeOnResize: false,
        rightBarStaysOnScroll: true,
      },
      rightPriceScale: {
        borderColor: themeOpts.rightPriceScale.borderColor,
        autoScale: true,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartApiRef.current = chart;

    // Candlestick Series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: themeOpts.series.upColor,
      downColor: themeOpts.series.downColor,
      borderVisible: false,
      wickUpColor: themeOpts.series.wickUpColor,
      wickDownColor: themeOpts.series.wickDownColor,
    });
    candlestickSeriesRef.current = candlestickSeries;

    candlestickSeries.setData(initialCandles.map((c: CandleData) => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    })));

    // Volume Series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeriesRef.current = volumeSeries;

    volumeSeries.setData(
      initialCandles.map((c: CandleData) => ({
        time: c.time,
        value: c.volume,
        color: c.close >= c.open ? themeOpts.series.volumeUp : themeOpts.series.volumeDown,
      }))
    );

    // Technical Overlay Indicators
    if (indicators.sma) {
      const smaData = calculateSMA(initialCandles, 20);
      const smaSeries = chart.addSeries(LineSeries, { color: '#ffb703', lineWidth: 2 });
      smaSeries.setData(smaData);
    }
    if (indicators.ema) {
      const emaData = calculateEMA(initialCandles, 30);
      const emaSeries = chart.addSeries(LineSeries, { color: '#387ed1', lineWidth: 2 });
      emaSeries.setData(emaData);
    }
    if (indicators.vwap) {
      const vwapData = calculateVWAP(initialCandles);
      const vwapSeries = chart.addSeries(LineSeries, { color: '#8c52ff', lineWidth: 2 });
      vwapSeries.setData(vwapData);
    }
    if (indicators.bollinger) {
      const bbData = calculateBollingerBands(initialCandles, 20, 2);
      const bbUpper = chart.addSeries(LineSeries, { color: 'rgba(56, 126, 209, 0.6)', lineWidth: 1 });
      const bbLower = chart.addSeries(LineSeries, { color: 'rgba(56, 126, 209, 0.6)', lineWidth: 1 });
      const bbMiddle = chart.addSeries(LineSeries, { color: 'rgba(255, 183, 3, 0.6)', lineWidth: 1 });

      bbUpper.setData(bbData.map(b => ({ time: b.time, value: b.upper })));
      bbLower.setData(bbData.map(b => ({ time: b.time, value: b.lower })));
      bbMiddle.setData(bbData.map(b => ({ time: b.time, value: b.middle })));
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartContainerRef.current && chartApiRef.current) {
        try {
          chartApiRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
        } catch {
          // Ignore
        }
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartApiRef.current) {
        try {
          chartApiRef.current.remove();
        } catch {
          // Ignored
        }
        chartApiRef.current = null;
      }
    };
  }, [activeSymbol, timeframe, indicators, theme]);

  // Smooth Live Real-Time Ticker (Updates latest candle in-place WITHOUT destroying or resetting chart scroll position)
  useEffect(() => {
    const interval = setInterval(() => {
      setCandles(prevCandles => {
        if (!prevCandles || prevCandles.length === 0) return prevCandles;

        const updated = [...prevCandles];
        const lastIndex = updated.length - 1;
        const last = updated[lastIndex];

        const volatility = last.close * 0.0006;
        const priceDelta = (Math.random() - 0.495) * volatility;
        const newClose = Number(Math.max(1, last.close + priceDelta).toFixed(2));
        const newHigh = Number(Math.max(last.high, newClose).toFixed(2));
        const newLow = Number(Math.min(last.low, newClose).toFixed(2));
        const newVolume = last.volume + Math.floor(Math.random() * 45) + 5;

        const updatedLast = {
          ...last,
          close: newClose,
          high: newHigh,
          low: newLow,
          volume: newVolume,
        };

        updated[lastIndex] = updatedLast;

        // Smooth in-place update on canvas
        if (candlestickSeriesRef.current) {
          try {
            candlestickSeriesRef.current.update({
              time: updatedLast.time,
              open: updatedLast.open,
              high: updatedLast.high,
              low: updatedLast.low,
              close: updatedLast.close,
            });
          } catch {
            // Safe catch
          }
        }

        if (volumeSeriesRef.current) {
          try {
            const themeOpts = getChartThemeOptions(theme);
            volumeSeriesRef.current.update({
              time: updatedLast.time,
              value: updatedLast.volume,
              color: updatedLast.close >= updatedLast.open ? themeOpts.series.volumeUp : themeOpts.series.volumeDown,
            });
          } catch {
            // Safe catch
          }
        }

        return updated;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [theme]);

  // Handle Order Submit
  const handleExecuteOrder = (e: React.FormEvent) => {
    e.preventDefault();
    placeOrder(activeSymbol, orderSide, orderQty, orderPrice, 'MARKET');
    setShowOrderModal(false);
  };

  const toggleIndicator = (name: keyof typeof indicators) => {
    setIndicators(prev => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: GROWW_THEME.colors.bgMain,
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        color: GROWW_THEME.colors.textPrimary,
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* 1. TOP INDICES HEADER TICKER BAR */}
      <div
        style={{
          height: '42px',
          backgroundColor: GROWW_THEME.colors.bgSurface,
          borderBottom: `1px solid ${GROWW_THEME.colors.border}`,
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', overflowX: 'auto' }}>
          {headerTickers.map((t, idx) => (
            <div
              key={idx}
              onClick={() => setActiveSymbol(t.name.split(' ')[0])}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '4px',
                transition: 'var(--transition-fast)',
              }}
              className="groww-btn-secondary"
            >
              <span style={{ fontWeight: 700, color: GROWW_THEME.colors.textPrimary }}>{t.name}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t.price}</span>
              <span
                style={{
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  color: t.positive ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                }}
              >
                {t.change}
              </span>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: GROWW_THEME.colors.textSecondary,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
              }}
              title="Close Terminal"
            >
              <X size={20} />
            </button>
          )}
        </div>
      </div>

      {/* 2. CHART TOOLBAR HEADER */}
      <div
        style={{
          height: '48px',
          backgroundColor: GROWW_THEME.colors.bgSurface,
          borderBottom: `1px solid ${GROWW_THEME.colors.border}`,
          padding: '0 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Left Toolbar Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Symbol Title / Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={16} color={GROWW_THEME.colors.textMuted} />
            <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>{activeSymbol}</span>
          </div>

          <div style={{ width: '1px', height: '18px', backgroundColor: GROWW_THEME.colors.border }} />

          {/* Timeframes */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            {['1m', '3m', '5m', '15m', '1h', '1D'].map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                style={{
                  padding: '4px 8px',
                  borderRadius: '4px',
                  border: 'none',
                  backgroundColor: timeframe === tf ? GROWW_THEME.colors.greenBg : 'transparent',
                  color: timeframe === tf ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                {tf}
              </button>
            ))}
          </div>

          <div style={{ width: '1px', height: '18px', backgroundColor: GROWW_THEME.colors.border }} />

          {/* Indicators Button */}
          <button
            onClick={() => setShowIndicatorModal(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: '6px',
              backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${GROWW_THEME.colors.border}`,
              color: GROWW_THEME.colors.textPrimary,
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <SlidersHorizontal size={15} color={GROWW_THEME.colors.green} />
            <span>fx Indicators</span>
            <ChevronDown size={14} />
          </button>
        </div>

        {/* Right Toolbar Paper Trade Quick Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => {
              setOrderSide('BUY');
              setOrderPrice(livePrice);
              setShowOrderModal(true);
            }}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              backgroundColor: GROWW_THEME.colors.green,
              color: '#0c0d10',
              fontWeight: 700,
              fontSize: '0.82rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <ArrowUpRight size={16} />
            <span>BUY</span>
          </button>

          <button
            onClick={() => {
              setOrderSide('SELL');
              setOrderPrice(livePrice);
              setShowOrderModal(true);
            }}
            style={{
              padding: '6px 16px',
              borderRadius: '6px',
              backgroundColor: GROWW_THEME.colors.red,
              color: '#ffffff',
              fontWeight: 700,
              fontSize: '0.82rem',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <ArrowDownRight size={16} />
            <span>SELL</span>
          </button>
        </div>
      </div>

      {/* 3. MAIN TERMINAL BODY (LEFT DRAWINGS + CENTER CANVAS + RIGHT DOCK) */}
      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {/* LEFT DRAWING TOOLBAR */}
        <div
          style={{
            width: '48px',
            backgroundColor: GROWW_THEME.colors.bgSurface,
            borderRight: `1px solid ${GROWW_THEME.colors.border}`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '12px 0',
            gap: '12px',
          }}
        >
          {[
            { id: 'cursor', icon: MousePointer, label: 'Crosshair' },
            { id: 'line', icon: MinusSquare, label: 'Trend Line' },
            { id: 'text', icon: Type, label: 'Text Note' },
            { id: 'measure', icon: Ruler, label: 'Measure Risk' },
            { id: 'clear', icon: Trash2, label: 'Clear Drawings' },
          ].map(tool => {
            const Icon = tool.icon;
            const isActive = activeDrawingTool === tool.id;
            return (
              <button
                key={tool.id}
                onClick={() => {
                  if (tool.id === 'clear') {
                    alert('Canvas drawings cleared');
                  } else {
                    setActiveDrawingTool(tool.id);
                  }
                }}
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: isActive ? GROWW_THEME.colors.greenBg : 'transparent',
                  color: isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'var(--transition-fast)',
                }}
                title={tool.label}
              >
                <Icon size={18} />
              </button>
            );
          })}
        </div>

        {/* CENTER MAIN CHART CANVAS */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', backgroundColor: GROWW_THEME.colors.bgMain }}>
          {/* Live OHLC Header Status Overlay */}
          <div
            style={{
              position: 'absolute',
              top: 12,
              left: 16,
              zIndex: 20,
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              fontSize: '0.8rem',
              fontWeight: 600,
              pointerEvents: 'none',
              backgroundColor: 'rgba(22, 24, 30, 0.75)',
              padding: '6px 12px',
              borderRadius: '6px',
              backdropFilter: 'blur(4px)',
            }}
          >
            <span>{activeSymbol} · {timeframe} · NSE</span>
            <span style={{ color: GROWW_THEME.colors.textMuted }}>O:</span>
            <span>{currentCandle?.open.toFixed(2)}</span>
            <span style={{ color: GROWW_THEME.colors.textMuted }}>H:</span>
            <span>{currentCandle?.high.toFixed(2)}</span>
            <span style={{ color: GROWW_THEME.colors.textMuted }}>L:</span>
            <span>{currentCandle?.low.toFixed(2)}</span>
            <span style={{ color: GROWW_THEME.colors.textMuted }}>C:</span>
            <span style={{ color: priceChange >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
              {currentCandle?.close.toFixed(2)} ({priceChange >= 0 ? '+' : ''}{priceChangePercent}%)
            </span>
          </div>

          {/* Active Indicators Legend */}
          <div
            style={{
              position: 'absolute',
              top: 48,
              left: 16,
              zIndex: 20,
              display: 'flex',
              gap: '8px',
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
          >
            {indicators.sma && <span style={{ color: '#ffb703', background: 'rgba(255, 183, 3, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>SMA 20</span>}
            {indicators.ema && <span style={{ color: '#387ed1', background: 'rgba(56, 126, 209, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>EMA 50</span>}
            {indicators.vwap && <span style={{ color: '#8c52ff', background: 'rgba(140, 82, 255, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>VWAP</span>}
            {indicators.bollinger && <span style={{ color: '#00d09c', background: 'rgba(0, 208, 156, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>Bollinger Bands</span>}
          </div>

          {/* Lightweight Chart Render Area */}
          <div ref={chartContainerRef} style={{ width: '100%', flex: 1 }} />

          {/* Bottom Time Range Selector */}
          <div
            style={{
              height: '32px',
              borderTop: `1px solid ${GROWW_THEME.colors.border}`,
              backgroundColor: GROWW_THEME.colors.bgSurface,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 16px',
              fontSize: '0.75rem',
              color: GROWW_THEME.colors.textMuted,
            }}
          >
            <div style={{ display: 'flex', gap: '12px' }}>
              {[
                { range: '1D', tf: '5m' },
                { range: '5D', tf: '15m' },
                { range: '1M', tf: '1h' },
                { range: '3M', tf: '1D' },
                { range: '1Y', tf: '1D' },
                { range: '5Y', tf: '1D' },
              ].map(item => (
                <span
                  key={item.range}
                  onClick={() => {
                    setActiveTimeRange(item.range);
                    setTimeframe(item.tf);
                  }}
                  style={{
                    cursor: 'pointer',
                    fontWeight: activeTimeRange === item.range ? 800 : 500,
                    color: activeTimeRange === item.range ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                  }}
                  className="groww-btn-secondary"
                >
                  {item.range}
                </span>
              ))}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: GROWW_THEME.colors.green, fontWeight: 700, fontSize: '0.72rem' }}>● LIVE TICKING</span>
              <span>· % log auto</span>
            </div>
          </div>
        </div>

        {/* RIGHT SIDE CONTAINER (DOCK CONTENT PANEL + VERTICAL TAB BAR) */}
        <div
          style={{
            display: 'flex',
            borderLeft: `1px solid ${GROWW_THEME.colors.border}`,
            backgroundColor: GROWW_THEME.colors.bgSurface,
          }}
        >
          {/* 1. DOCK CONTENT PANEL (Shows when a tab is active) */}
          {activeDockTab && (
            <div
              style={{
                width: '360px',
                backgroundColor: GROWW_THEME.colors.bgSurface,
                borderRight: `1px solid ${GROWW_THEME.colors.border}`,
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
              }}
            >
              {/* Header Bar matching image: Grip dots + Title + Close Button */}
              <div
                style={{
                  height: '42px',
                  borderBottom: `1px solid ${GROWW_THEME.colors.border}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0 12px 0 16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <GripVertical size={16} color={GROWW_THEME.colors.textMuted} style={{ cursor: 'grab' }} />
                  <span style={{ fontSize: '0.9rem', fontWeight: 700, color: GROWW_THEME.colors.textPrimary }}>
                    {activeDockTab === 'chain' && 'Chain'}
                    {activeDockTab === 'positions' && `Positions (${positions.length})`}
                    {activeDockTab === 'orders' && `Orders (${orders.length})`}
                    {activeDockTab === 'depth' && 'Depth'}
                    {activeDockTab === 'balance' && 'Balance'}
                    {activeDockTab === 'watchlist' && 'Watchlist'}
                  </span>
                </div>
                <button
                  onClick={() => setActiveDockTab(null)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: GROWW_THEME.colors.textMuted,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '4px',
                    borderRadius: '4px',
                    transition: 'var(--transition-fast)',
                  }}
                  className="groww-btn-secondary"
                  title="Close Panel"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Dock Content Body */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
                {/* TAB 1: OPTION CHAIN */}
                {activeDockTab === 'chain' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>NIFTY Option Chain</span>
                      <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.green, fontWeight: 600 }}>04 Aug Expiry</span>
                    </div>

                    <div className="groww-table-wrapper">
                      <table className="groww-table" style={{ fontSize: '0.8rem' }}>
                        <thead>
                          <tr>
                            <th style={{ padding: '8px' }}>Call LTP</th>
                            <th style={{ padding: '8px', textAlign: 'center' }}>Strike</th>
                            <th style={{ padding: '8px', textAlign: 'right' }}>Put LTP</th>
                          </tr>
                        </thead>
                        <tbody>
                          {optionChain.slice(3, 11).map((opt: OptionStrikeData, idx: number) => {
                            const isAtm = Math.abs(opt.strike - 24350) < 25;
                            return (
                              <tr key={idx} style={{ backgroundColor: isAtm ? 'rgba(0, 208, 156, 0.08)' : 'transparent' }}>
                                <td style={{ padding: '8px', color: GROWW_THEME.colors.green, fontWeight: 600 }}>
                                  ₹{opt.callLtp.toFixed(2)}
                                </td>
                                <td style={{ padding: '8px', textAlign: 'center', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                                  {opt.strike}
                                </td>
                                <td style={{ padding: '8px', textAlign: 'right', color: GROWW_THEME.colors.red, fontWeight: 600 }}>
                                  ₹{opt.putLtp.toFixed(2)}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB 2: POSITIONS */}
                {activeDockTab === 'positions' && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700 }}>Open Paper Positions</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: totalPnl >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                        P&L: ₹{totalPnl.toFixed(2)}
                      </span>
                    </div>

                    {positions.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '32px 0', color: GROWW_THEME.colors.textMuted, fontSize: '0.85rem' }}>
                        No open paper trading positions. Click BUY or SELL above to trade!
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {positions.map(pos => (
                          <div
                            key={pos.id}
                            style={{
                              backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                              border: `1px solid ${GROWW_THEME.colors.border}`,
                              borderRadius: '8px',
                              padding: '12px',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                              <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{pos.symbol}</span>
                              <span
                                style={{
                                  fontSize: '0.72rem',
                                  fontWeight: 700,
                                  padding: '2px 6px',
                                  borderRadius: '4px',
                                  backgroundColor: pos.side === 'BUY' ? GROWW_THEME.colors.greenBg : GROWW_THEME.colors.redBg,
                                  color: pos.side === 'BUY' ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                                }}
                              >
                                {pos.side} {pos.qty} Qty
                              </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: GROWW_THEME.colors.textSecondary, marginBottom: '8px' }}>
                              <span>Entry: ₹{pos.entryPrice.toFixed(2)}</span>
                              <span>LTP: ₹{pos.currentPrice.toFixed(2)}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: 700, fontSize: '0.9rem', color: pos.pnl >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                                ₹{pos.pnl.toFixed(2)} ({pos.pnlPercent.toFixed(2)}%)
                              </span>
                              <button
                                onClick={() => closePosition(pos.id)}
                                style={{
                                  padding: '4px 10px',
                                  borderRadius: '4px',
                                  backgroundColor: GROWW_THEME.colors.redBg,
                                  color: GROWW_THEME.colors.red,
                                  border: `1px solid ${GROWW_THEME.colors.redBorder}`,
                                  fontWeight: 600,
                                  fontSize: '0.75rem',
                                  cursor: 'pointer',
                                }}
                              >
                                Close
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 3: ORDERS */}
                {activeDockTab === 'orders' && (
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, display: 'block', marginBottom: '12px' }}>Executed Paper Orders</span>
                    {orders.length === 0 ? (
                      <div style={{ textAlign: 'center', padding: '32px 0', color: GROWW_THEME.colors.textMuted, fontSize: '0.85rem' }}>
                        No order history recorded yet.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {orders.map(ord => (
                          <div
                            key={ord.id}
                            style={{
                              backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                              border: `1px solid ${GROWW_THEME.colors.border}`,
                              borderRadius: '6px',
                              padding: '10px 12px',
                              fontSize: '0.8rem',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, marginBottom: '4px' }}>
                              <span style={{ color: ord.side === 'BUY' ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                                {ord.side} {ord.qty} x {ord.symbol}
                              </span>
                              <span>₹{ord.price.toFixed(2)}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', color: GROWW_THEME.colors.textMuted, fontSize: '0.72rem' }}>
                              <span>{ord.type} · {ord.status}</span>
                              <span>{ord.timestamp}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 4: DEPTH (LEVEL 2 ORDER BOOK) */}
                {activeDockTab === 'depth' && (
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, display: 'block', marginBottom: '12px' }}>Market Depth (Level 2)</span>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.78rem' }}>
                      {/* Bids */}
                      <div>
                        <span style={{ fontWeight: 700, color: GROWW_THEME.colors.green, display: 'block', marginBottom: '6px' }}>Bids (Buy)</span>
                        {[
                          { price: livePrice - 0.5, qty: 1450 },
                          { price: livePrice - 1.2, qty: 2890 },
                          { price: livePrice - 2.0, qty: 4120 },
                          { price: livePrice - 3.5, qty: 6500 },
                        ].map((b, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                            <span>₹{b.price.toFixed(2)}</span>
                            <span style={{ color: GROWW_THEME.colors.textMuted }}>{b.qty}</span>
                          </div>
                        ))}
                      </div>

                      {/* Asks */}
                      <div>
                        <span style={{ fontWeight: 700, color: GROWW_THEME.colors.red, display: 'block', marginBottom: '6px' }}>Asks (Sell)</span>
                        {[
                          { price: livePrice + 0.5, qty: 1120 },
                          { price: livePrice + 1.1, qty: 3100 },
                          { price: livePrice + 2.4, qty: 5400 },
                          { price: livePrice + 3.8, qty: 8900 },
                        ].map((a, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                            <span>₹{a.price.toFixed(2)}</span>
                            <span style={{ color: GROWW_THEME.colors.textMuted }}>{a.qty}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 5: BALANCE */}
                {activeDockTab === 'balance' && (
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, display: 'block', marginBottom: '12px' }}>Paper Trading Wallet</span>
                    <div
                      style={{
                        backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                        border: `1px solid ${GROWW_THEME.colors.border}`,
                        borderRadius: '8px',
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: GROWW_THEME.colors.textSecondary, fontSize: '0.8rem' }}>Total Funds</span>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>₹{balance.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: GROWW_THEME.colors.textSecondary, fontSize: '0.8rem' }}>Available Margin</span>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: GROWW_THEME.colors.green }}>
                          ₹{availableMargin.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: GROWW_THEME.colors.textSecondary, fontSize: '0.8rem' }}>Used Margin</span>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>₹{usedMargin.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '8px', borderTop: `1px solid ${GROWW_THEME.colors.border}` }}>
                        <span style={{ color: GROWW_THEME.colors.textSecondary, fontSize: '0.8rem' }}>Total Unrealized P&L</span>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: totalPnl >= 0 ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                          ₹{totalPnl.toFixed(2)}
                        </span>
                      </div>

                      <button
                        onClick={resetAccount}
                        className="groww-btn groww-btn-secondary"
                        style={{ marginTop: '8px', width: '100%', fontSize: '0.8rem', padding: '8px' }}
                      >
                        Reset Virtual Account (₹10 Lakhs)
                      </button>
                    </div>
                  </div>
                )}

                {/* TAB 6: WATCHLIST */}
                {activeDockTab === 'watchlist' && (
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, display: 'block', marginBottom: '12px' }}>Market Watchlist</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {[
                        { sym: 'NIFTY 50', price: '24,383.60', chg: '+66.45 (+0.27%)', pos: true },
                        { sym: 'BANK NIFTY', price: '52,140.35', chg: '+117.35 (+0.21%)', pos: true },
                        { sym: 'FINNIFTY', price: '23,450.10', chg: '+45.20 (+0.19%)', pos: true },
                        { sym: 'SENSEX', price: '78,094.64', chg: '+166.49 (+0.21%)', pos: true },
                        { sym: 'RELIANCE', price: '₹3,024.50', chg: '+18.40 (+0.61%)', pos: true },
                        { sym: 'TCS', price: '₹4,180.00', chg: '-12.50 (-0.30%)', pos: false },
                      ].map((item, idx) => (
                        <div
                          key={idx}
                          onClick={() => setActiveSymbol(item.sym)}
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px 12px',
                            backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                            border: `1px solid ${GROWW_THEME.colors.border}`,
                            borderRadius: '6px',
                            cursor: 'pointer',
                          }}
                        >
                          <div>
                            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{item.sym}</div>
                            <div style={{ fontSize: '0.72rem', color: GROWW_THEME.colors.textMuted }}>NSE Index</div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{item.price}</div>
                            <div style={{ fontSize: '0.72rem', color: item.pos ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                              {item.chg}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 2. RIGHT VERTICAL TOOLBAR NAVIGATION (Matches image layout) */}
          <div
            style={{
              width: '72px',
              backgroundColor: GROWW_THEME.colors.bgSurface,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '12px 0',
              gap: '14px',
              userSelect: 'none',
            }}
          >
            {[
              { id: 'positions' as DockTab, label: 'Positions', icon: Briefcase, count: positions.length },
              { id: 'chain' as DockTab, label: 'Chain', icon: Layers },
              { id: 'orders' as DockTab, label: 'Orders', icon: History, count: orders.length },
              { id: 'watchlist' as DockTab, label: 'Watchlist', icon: Search },
              { id: 'depth' as DockTab, label: 'Depth', icon: BarChart2 },
              { id: 'balance' as DockTab, label: 'Balance', icon: Wallet },
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeDockTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveDockTab(prev => (prev === tab.id ? null : tab.id))}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: 'none',
                    background: 'transparent',
                    width: '100%',
                    cursor: 'pointer',
                    padding: '2px 0',
                    outline: 'none',
                  }}
                  title={tab.label}
                >
                  {/* Rounded icon pill container like image */}
                  <div
                    style={{
                      width: '38px',
                      height: '38px',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: isActive ? GROWW_THEME.colors.greenBg : 'transparent',
                      color: isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                      transition: 'all 0.15s ease-in-out',
                      position: 'relative',
                    }}
                  >
                    <Icon size={18} />
                    {tab.count !== undefined && tab.count > 0 && (
                      <span
                        style={{
                          position: 'absolute',
                          top: '2px',
                          right: '2px',
                          backgroundColor: GROWW_THEME.colors.green,
                          color: '#0c0d10',
                          fontSize: '0.65rem',
                          fontWeight: 800,
                          borderRadius: '50%',
                          width: '14px',
                          height: '14px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {tab.count}
                      </span>
                    )}
                  </div>
                  {/* Label under icon like image */}
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: isActive ? 700 : 500,
                      marginTop: '3px',
                      color: isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                      textAlign: 'center',
                      lineHeight: 1.1,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 4. INDICATORS SELECTOR MODAL */}
      {showIndicatorModal && (
        <div className="modal-overlay" onClick={() => setShowIndicatorModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '440px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Technical Indicators</h3>
              <button onClick={() => setShowIndicatorModal(false)} style={{ background: 'none', border: 'none', color: GROWW_THEME.colors.textMuted, cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                { key: 'sma', label: 'Simple Moving Average (SMA 20)', color: '#ffb703' },
                { key: 'ema', label: 'Exponential Moving Average (EMA 50)', color: '#387ed1' },
                { key: 'vwap', label: 'Volume Weighted Average Price (VWAP)', color: '#8c52ff' },
                { key: 'bollinger', label: 'Bollinger Bands (20, 2)', color: '#00d09c' },
              ].map(ind => {
                const isChecked = indicators[ind.key as keyof typeof indicators];
                return (
                  <div
                    key={ind.key}
                    onClick={() => toggleIndicator(ind.key as keyof typeof indicators)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      borderRadius: '8px',
                      backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                      border: `1px solid ${isChecked ? ind.color : GROWW_THEME.colors.border}`,
                      cursor: 'pointer',
                    }}
                  >
                    <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{ind.label}</span>
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '4px',
                        backgroundColor: isChecked ? ind.color : 'transparent',
                        border: `1px solid ${ind.color}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {isChecked && <Check size={14} color="#0c0d10" strokeWidth={3} />}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 5. PAPER TRADING ORDER FORM MODAL */}
      {showOrderModal && (
        <div className="modal-overlay" onClick={() => setShowOrderModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '400px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: orderSide === 'BUY' ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                {orderSide} {activeSymbol}
              </h3>
              <button onClick={() => setShowOrderModal(false)} style={{ background: 'none', border: 'none', color: GROWW_THEME.colors.textMuted, cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleExecuteOrder} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Quantity (Lots)</label>
                <input
                  type="number"
                  value={orderQty}
                  onChange={e => setOrderQty(Number(e.target.value))}
                  className="groww-input"
                  style={{ width: '100%' }}
                  min={1}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Execution Price</label>
                <input
                  type="number"
                  value={orderPrice}
                  onChange={e => setOrderPrice(Number(e.target.value))}
                  className="groww-input"
                  style={{ width: '100%' }}
                  step="0.05"
                />
              </div>

              <div style={{ padding: '10px', backgroundColor: GROWW_THEME.colors.bgSurfaceHover, borderRadius: '6px', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: GROWW_THEME.colors.textMuted }}>Required Margin:</span>
                  <span style={{ fontWeight: 700 }}>₹{(orderQty * orderPrice).toFixed(2)}</span>
                </div>
              </div>

              <button
                type="submit"
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: '6px',
                  backgroundColor: orderSide === 'BUY' ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                  color: orderSide === 'BUY' ? '#0c0d10' : '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  border: 'none',
                  cursor: 'pointer',
                  marginTop: '8px',
                }}
              >
                Place Paper {orderSide} Order
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProTradingTerminal;

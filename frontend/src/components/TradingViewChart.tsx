import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import type { CandleData } from '../utils/mockMarketData';
import { GROWW_THEME, getChartThemeOptions } from '../utils/theme';
import { useTheme } from '../context/ThemeContext';

interface TradingViewChartProps {
  candles: CandleData[];
  title?: string;
  height?: number;
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  candles,
  title,
  height = 440,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const { theme } = useTheme();

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const themeOpts = getChartThemeOptions(theme);

    // Initialize Lightweight Chart Engine
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: themeOpts.layout.background.color },
        textColor: themeOpts.layout.textColor,
        fontFamily: themeOpts.layout.fontFamily,
      },
      grid: themeOpts.grid,
      crosshair: themeOpts.crosshair,
      timeScale: themeOpts.timeScale,
      rightPriceScale: themeOpts.rightPriceScale,
    });

    chartRef.current = chart;

    // Add Candlestick Series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: themeOpts.series.upColor,
      downColor: themeOpts.series.downColor,
      borderVisible: false,
      wickUpColor: themeOpts.series.wickUpColor,
      wickDownColor: themeOpts.series.wickDownColor,
    });

    // Add Volume Histogram Series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: themeOpts.series.upColor,
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // overlay
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.8, // volume takes bottom 20%
        bottom: 0,
      },
    });

    // Format candle data for chart engine
    const formattedCandles = candles.map(c => ({
      time: c.time,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    const formattedVolume = candles.map(c => ({
      time: c.time,
      value: c.volume,
      color: c.close >= c.open ? themeOpts.series.volumeUp : themeOpts.series.volumeDown,
    }));

    candlestickSeries.setData(formattedCandles);
    volumeSeries.setData(formattedVolume);

    chart.timeScale().fitContent();

    // Responsive resize handler
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [candles, height, theme]);

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      {title && (
        <div style={{ position: 'absolute', top: 12, left: 16, zIndex: 10, pointerEvents: 'none' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: GROWW_THEME.colors.textMuted }}>
            {title} (TradingView Lightweight Engine)
          </span>
        </div>
      )}
      <div ref={chartContainerRef} style={{ width: '100%', height }} />
    </div>
  );
};

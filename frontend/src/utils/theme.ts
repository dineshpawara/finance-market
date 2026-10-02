import { LineStyle, type LineWidth } from 'lightweight-charts';

/**
 * Groww App Design System Tokens using CSS Custom Properties
 */
export const GROWW_THEME = {
  colors: {
    bgMain: 'var(--bg-main)',
    bgSurface: 'var(--bg-surface)',
    bgSurfaceHover: 'var(--bg-surface-hover)',
    border: 'var(--border-color)',
    borderSubtle: 'var(--border-subtle)',
    green: 'var(--groww-green)',
    greenBg: 'var(--groww-green-bg)',
    greenBorder: 'var(--groww-green-border)',
    red: 'var(--bear-red)',
    redBg: 'var(--bear-red-bg)',
    redBorder: 'var(--bear-red-border)',
    textPrimary: 'var(--text-primary)',
    textSecondary: 'var(--text-secondary)',
    textMuted: 'var(--text-muted)',
    blue: 'var(--accent-blue)',
    yellow: 'var(--accent-yellow)',
  },
  chartOptions: {
    layout: {
      background: { color: '#16181e' },
      textColor: '#9e9e9e',
      fontSize: 12,
      fontFamily: 'Inter, sans-serif',
    },
    grid: {
      vertLines: { color: '#252932', style: LineStyle.Solid },
      horzLines: { color: '#252932', style: LineStyle.Solid },
    },
    crosshair: {
      vertLine: { color: '#00d09c', width: 1 as LineWidth, style: LineStyle.Dashed, labelBackgroundColor: '#00d09c' },
      horzLine: { color: '#00d09c', width: 1 as LineWidth, style: LineStyle.Dashed, labelBackgroundColor: '#00d09c' },
    },
    timeScale: {
      borderColor: '#252932',
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: '#252932',
    },
  },
};

export const getChartThemeOptions = (theme: 'dark' | 'light') => {
  const isDark = theme === 'dark';
  const greenColor = isDark ? '#00d09c' : '#00a87d';
  const redColor = isDark ? '#eb5757' : '#df2020';
  const bgSurface = isDark ? '#16181e' : '#ffffff';
  const textSecondary = isDark ? '#9e9e9e' : '#475569';
  const borderColor = isDark ? '#252932' : '#e2e8f0';

  return {
    layout: {
      background: { color: bgSurface },
      textColor: textSecondary,
      fontSize: 12,
      fontFamily: 'Inter, sans-serif',
    },
    grid: {
      vertLines: { color: borderColor, style: LineStyle.Solid },
      horzLines: { color: borderColor, style: LineStyle.Solid },
    },
    crosshair: {
      vertLine: { color: greenColor, width: 1 as LineWidth, style: LineStyle.Dashed, labelBackgroundColor: greenColor },
      horzLine: { color: greenColor, width: 1 as LineWidth, style: LineStyle.Dashed, labelBackgroundColor: greenColor },
    },
    timeScale: {
      borderColor: borderColor,
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: borderColor,
    },
    series: {
      upColor: greenColor,
      downColor: redColor,
      wickUpColor: greenColor,
      wickDownColor: redColor,
      volumeUp: isDark ? 'rgba(0, 208, 156, 0.35)' : 'rgba(0, 168, 125, 0.35)',
      volumeDown: isDark ? 'rgba(235, 87, 87, 0.35)' : 'rgba(223, 32, 32, 0.35)',
    },
  };
};

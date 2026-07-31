import React from 'react';
import { X, TrendingUp, TrendingDown, Building } from 'lucide-react';
import type { CandleData, NiftyStockItem } from '../utils/mockMarketData';
import { TradingViewChart } from './TradingViewChart';
import { formatINR, formatPercent, formatVolume } from '../utils/formatters';
import { GROWW_THEME } from '../utils/theme';

interface StockDetailModalProps {
  stock: NiftyStockItem | null;
  candles: CandleData[];
  onClose: () => void;
}

export const StockDetailModal: React.FC<StockDetailModalProps> = ({
  stock,
  candles,
  onClose,
}) => {
  if (!stock) return null;

  const isPositive = stock.change >= 0;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: `1px solid ${GROWW_THEME.colors.border}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h2 style={{ fontSize: '1.4rem' }}>{stock.name}</h2>
              <span className="mono" style={{ fontSize: '0.85rem', padding: '2px 8px', borderRadius: '4px', background: GROWW_THEME.colors.bgSurfaceHover, color: GROWW_THEME.colors.textMuted }}>
                {stock.symbol}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <Building size={14} color={GROWW_THEME.colors.textMuted} />
              <span style={{ fontSize: '0.8rem', color: GROWW_THEME.colors.textMuted }}>{stock.sector}</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, fontFamily: 'JetBrains Mono' }}>
                {formatINR(stock.price)}
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '4px',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: isPositive ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                }}
              >
                {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                <span>{formatINR(stock.change)} ({formatPercent(stock.changePercent)})</span>
              </div>
            </div>

            <button
              onClick={onClose}
              style={{
                background: GROWW_THEME.colors.bgSurfaceHover,
                border: `1px solid ${GROWW_THEME.colors.border}`,
                color: GROWW_THEME.colors.textSecondary,
                borderRadius: '50%',
                width: '36px',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px' }}>
          {/* Key Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
            <div style={{ padding: '12px', borderRadius: '8px', background: GROWW_THEME.colors.bgSurfaceHover, border: `1px solid ${GROWW_THEME.colors.border}` }}>
              <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>Day High / Low</span>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono', marginTop: '2px' }}>
                ₹{stock.high} / ₹{stock.low}
              </div>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: GROWW_THEME.colors.bgSurfaceHover, border: `1px solid ${GROWW_THEME.colors.border}` }}>
              <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>52W High / Low</span>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono', marginTop: '2px' }}>
                ₹{stock.high52} / ₹{stock.low52}
              </div>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: GROWW_THEME.colors.bgSurfaceHover, border: `1px solid ${GROWW_THEME.colors.border}` }}>
              <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>Volume</span>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono', marginTop: '2px' }}>
                {formatVolume(stock.volume)}
              </div>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: GROWW_THEME.colors.bgSurfaceHover, border: `1px solid ${GROWW_THEME.colors.border}` }}>
              <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>Market Cap / P/E</span>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono', marginTop: '2px' }}>
                ₹{(stock.marketCapCr / 1000).toFixed(1)}k Cr / {stock.pe}x
              </div>
            </div>
          </div>

          {/* Candlestick Chart */}
          <div className="groww-card" style={{ padding: '12px' }}>
            <h4 style={{ fontSize: '0.95rem', marginBottom: '12px', color: GROWW_THEME.colors.textSecondary }}>
              Interactive Candlestick Chart
            </h4>
            <TradingViewChart candles={candles} title={`${stock.symbol} Price Chart`} height={360} />
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { Globe, TrendingUp, TrendingDown } from 'lucide-react';
import type { GlobalMarketItem } from '../utils/mockMarketData';
import { formatNumber, formatPercent } from '../utils/formatters';
import { GROWW_THEME } from '../utils/theme';

interface GlobalMarketCardProps {
  markets: GlobalMarketItem[];
}

export const GlobalMarketCard: React.FC<GlobalMarketCardProps> = ({ markets }) => {
  return (
    <div className="groww-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="groww-card-header">
        <div className="groww-card-title">
          <Globe size={20} color={GROWW_THEME.colors.blue} />
          <span>Global Markets Price Action</span>
        </div>
        <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted, fontWeight: 500 }}>
          Real-time Indices & Commodities
        </span>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
        {markets.map(m => {
          const isPositive = m.change >= 0;
          return (
            <div
              key={m.symbol}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: '8px',
                backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                border: `1px solid ${GROWW_THEME.colors.border}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.1rem' }}>{m.flag}</span>
                <div>
                  <h5 style={{ fontSize: '0.88rem', fontWeight: 600, color: GROWW_THEME.colors.textPrimary }}>
                    {m.name}
                  </h5>
                  <span style={{ fontSize: '0.7rem', color: GROWW_THEME.colors.textMuted }}>{m.region}</span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                  {formatNumber(m.price)}
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    color: isPositive ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                  }}
                >
                  {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                  <span>{formatPercent(m.changePercent)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

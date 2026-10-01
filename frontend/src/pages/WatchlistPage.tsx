import React from 'react';
import { GROWW_THEME } from '../utils/theme';
import { Bookmark, Plus } from 'lucide-react';
import { MOCK_NIFTY50_STOCKS } from '../utils/mockMarketData';
import { formatINR, formatPercent } from '../utils/formatters';

export const WatchlistPage: React.FC = () => {
  const watchlist = MOCK_NIFTY50_STOCKS.slice(0, 6);

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Personal Watchlist</h1>
          <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textMuted }}>
            Track your favorite Indian equities, alerts and price movements
          </p>
        </div>

        <button className="groww-btn groww-btn-primary" style={{ height: '38px', fontSize: '0.85rem' }}>
          <Plus size={16} />
          <span>Add Symbol</span>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {watchlist.map(st => (
          <div key={st.symbol} className="groww-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>{st.symbol}</h3>
                <span style={{ fontSize: '0.78rem', color: GROWW_THEME.colors.textMuted }}>{st.sector}</span>
              </div>
              <Bookmark size={18} color={GROWW_THEME.colors.green} fill={GROWW_THEME.colors.green} />
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: '8px' }}>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, fontFamily: 'JetBrains Mono' }}>
                {formatINR(st.price)}
              </div>
              <span className={`trend-badge ${st.change >= 0 ? 'positive' : 'negative'}`}>
                {formatPercent(st.changePercent)}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted, paddingTop: '8px', borderTop: `1px solid ${GROWW_THEME.colors.border}` }}>
              <span>High: ₹{st.high}</span>
              <span>Low: ₹{st.low}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

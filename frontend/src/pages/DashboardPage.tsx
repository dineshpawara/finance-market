import React from 'react';
import { useDashboardController } from '../controller/dashboardController';
import { NewsCard } from '../components/NewsCard';
import { GlobalMarketCard } from '../components/GlobalMarketCard';
import { TradingViewChart } from '../components/TradingViewChart';
import { GROWW_THEME } from '../utils/theme';
import { BarChart3, RefreshCw } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const {
    selectedIndex,
    availableIndices,
    candles,
    globalMarkets,
    newsItems,
    sentiment,
    timeframe,
    loading,
    handleIndexChange,
    handleTimeframeChange,
    refreshDashboard,
  } = useDashboardController();

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Market Overview Dashboard</h1>
          <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textMuted }}>
            Real-time Indian indices, global markets, sentiment feed & technical analysis
          </p>
        </div>

        <button
          onClick={refreshDashboard}
          className="groww-btn groww-btn-secondary"
          style={{ height: '38px', fontSize: '0.85rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Top Grid: News & Global Markets */}
      <div className="dashboard-grid">
        {/* Top Left Card: News Feed */}
        <div className="dash-top-left">
          <NewsCard newsItems={newsItems} sentiment={sentiment} onRefresh={refreshDashboard} isRefreshing={loading} />
        </div>

        {/* Top Right Card: Global Market Price Action */}
        <div className="dash-top-right">
          <GlobalMarketCard markets={globalMarkets} />
        </div>

        {/* Bottom Card: Full-width Live TradingView Chart */}
        <div className="dash-chart-card">
          <div className="groww-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Chart Control Header */}
            <div className="groww-card-header" style={{ marginBottom: 0 }}>
              <div className="groww-card-title">
                <BarChart3 size={22} color={GROWW_THEME.colors.green} />
                <span>Live Index Candlestick Chart</span>

                {/* Index Selector Dropdown */}
                <select
                  value={selectedIndex}
                  onChange={(e) => handleIndexChange(e.target.value)}
                  className="groww-select"
                  style={{ fontWeight: 700, fontSize: '0.95rem', marginLeft: '10px' }}
                >
                  {availableIndices.map((idx) => (
                    <option key={idx} value={idx}>
                      {idx}
                    </option>
                  ))}
                </select>
              </div>

              {/* Timeframe Selector Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                {['1D', '1W', '1M', '1Y'].map((tf) => (
                  <button
                    key={tf}
                    onClick={() => handleTimeframeChange(tf)}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '6px',
                      border: `1px solid ${timeframe === tf ? GROWW_THEME.colors.greenBorder : GROWW_THEME.colors.border}`,
                      backgroundColor: timeframe === tf ? GROWW_THEME.colors.greenBg : GROWW_THEME.colors.bgSurfaceHover,
                      color: timeframe === tf ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>

            {/* TradingView Chart Component */}
            {loading ? (
              <div style={{ height: '440px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: GROWW_THEME.colors.textMuted }}>
                Loading TradingView Engine...
              </div>
            ) : (
              <TradingViewChart candles={candles} title={selectedIndex} height={440} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import { useNifty50Controller } from '../controller/nifty50Controller';
import { StockDetailModal } from '../components/StockDetailModal';
import { formatINR, formatPercent, formatVolume } from '../utils/formatters';
import { GROWW_THEME } from '../utils/theme';
import { Search, Filter, TrendingUp, TrendingDown, Eye } from 'lucide-react';

export const Nifty50Page: React.FC = () => {
  const {
    stocks,
    sectors,
    searchQuery,
    selectedSector,
    selectedStock,
    stockCandles,
    loading,
    handleSearchChange,
    handleSectorChange,
    handleSelectStock,
  } = useNifty50Controller();

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Nifty 50 Stock Analysis</h1>
          <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textMuted }}>
            Real-time price actions for top 50 Indian bluechip companies. Click any stock to launch interactive chart.
          </p>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Search */}
          <div style={{ position: 'relative', width: '240px' }}>
            <Search size={16} color={GROWW_THEME.colors.textMuted} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search symbol or name..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="groww-input"
              style={{ width: '100%', paddingLeft: '36px', height: '38px' }}
            />
          </div>

          {/* Sector Select */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={16} color={GROWW_THEME.colors.textMuted} />
            <select
              value={selectedSector}
              onChange={(e) => handleSectorChange(e.target.value)}
              className="groww-select"
              style={{ height: '38px' }}
            >
              {sectors.map((sec) => (
                <option key={sec} value={sec}>
                  {sec === 'ALL' ? 'All Sectors' : sec}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stock Table */}
      <div className="groww-table-wrapper">
        <table className="groww-table">
          <thead>
            <tr>
              <th>COMPANY</th>
              <th>SECTOR</th>
              <th style={{ textAlign: 'right' }}>LTP (₹)</th>
              <th style={{ textAlign: 'right' }}>CHANGE</th>
              <th style={{ textAlign: 'right' }}>DAY HIGH / LOW</th>
              <th style={{ textAlign: 'right' }}>52W HIGH / LOW</th>
              <th style={{ textAlign: 'right' }}>VOLUME</th>
              <th style={{ textAlign: 'center' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: GROWW_THEME.colors.textMuted }}>
                  Loading Nifty 50 stocks...
                </td>
              </tr>
            ) : stocks.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '30px', color: GROWW_THEME.colors.textMuted }}>
                  No stocks matching filter criteria
                </td>
              </tr>
            ) : (
              stocks.map((stock) => {
                const isPositive = stock.change >= 0;
                return (
                  <tr key={stock.symbol} onClick={() => handleSelectStock(stock)}>
                    <td>
                      <div>
                        <span style={{ fontWeight: 700, fontSize: '0.92rem', color: GROWW_THEME.colors.textPrimary }}>
                          {stock.symbol}
                        </span>
                        <div style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>
                          {stock.name}
                        </div>
                      </div>
                    </td>

                    <td>
                      <span style={{ fontSize: '0.78rem', padding: '3px 8px', borderRadius: '4px', background: GROWW_THEME.colors.bgSurfaceHover, color: GROWW_THEME.colors.textSecondary }}>
                        {stock.sector}
                      </span>
                    </td>

                    <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono', fontWeight: 700 }}>
                      {formatINR(stock.price)}
                    </td>

                    <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontWeight: 700,
                          color: isPositive ? GROWW_THEME.colors.green : GROWW_THEME.colors.red,
                        }}
                      >
                        {isPositive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                        {formatINR(stock.change)} ({formatPercent(stock.changePercent)})
                      </span>
                    </td>

                    <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono', fontSize: '0.82rem', color: GROWW_THEME.colors.textSecondary }}>
                      ₹{stock.high} / ₹{stock.low}
                    </td>

                    <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono', fontSize: '0.82rem', color: GROWW_THEME.colors.textMuted }}>
                      ₹{stock.high52} / ₹{stock.low52}
                    </td>

                    <td style={{ textAlign: 'right', fontFamily: 'JetBrains Mono', fontSize: '0.82rem' }}>
                      {formatVolume(stock.volume)}
                    </td>

                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectStock(stock);
                        }}
                        style={{
                          background: GROWW_THEME.colors.greenBg,
                          border: `1px solid ${GROWW_THEME.colors.greenBorder}`,
                          color: GROWW_THEME.colors.green,
                          borderRadius: '6px',
                          padding: '6px 10px',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        <Eye size={14} />
                        <span>Chart</span>
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Stock Detail Modal */}
      <StockDetailModal
        stock={selectedStock}
        candles={stockCandles}
        onClose={() => handleSelectStock(null)}
      />
    </div>
  );
};

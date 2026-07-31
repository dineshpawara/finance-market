import React from 'react';
import { useOptionChainController } from '../controller/optionChainController';
import { OptionChainTable } from '../components/OptionChainTable';
import { GROWW_THEME } from '../utils/theme';
import { RefreshCw } from 'lucide-react';

export const OptionChainPage: React.FC = () => {
  const {
    underlying,
    availableIndices,
    optionChain,
    selectedExpiry,
    loading,
    handleUnderlyingChange,
    handleExpiryChange,
    refreshOptionChain,
  } = useOptionChainController();

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800 }}>Indian Options Analytics</h1>
          <p style={{ fontSize: '0.88rem', color: GROWW_THEME.colors.textMuted }}>
            Full Option Chain matrix with Open Interest (OI), Implied Volatility (IV), PCR & Max Pain analysis
          </p>
        </div>

        <button
          onClick={refreshOptionChain}
          className="groww-btn groww-btn-secondary"
          style={{ height: '38px', fontSize: '0.85rem' }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh Matrix</span>
        </button>
      </div>

      <OptionChainTable
        data={optionChain}
        selectedExpiry={selectedExpiry}
        onExpiryChange={handleExpiryChange}
        underlying={underlying}
        onUnderlyingChange={handleUnderlyingChange}
        availableIndices={availableIndices}
      />
    </div>
  );
};

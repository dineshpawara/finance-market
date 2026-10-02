import React, { useState } from 'react';
import { Search, Bell, User, Zap, Sun, Moon, Maximize2 } from 'lucide-react';
import { GROWW_THEME } from '../utils/theme';
import { useTheme } from '../context/ThemeContext';
import { ProTradingTerminal } from './ProTradingTerminal';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [activeTerminalSymbol, setActiveTerminalSymbol] = useState<string | null>(null);

  const headerIndices = [
    { name: 'NIFTY 50', price: '24,852.15', change: '+124.50 (0.50%)', positive: true },
    { name: 'SENSEX', price: '81,450.80', change: '+340.20 (0.42%)', positive: true },
    // { name: 'BANK NIFTY', price: '52,140.35', change: '+210.80 (0.41%)', positive: true },
  ];

  return (
    <>
      <header
        style={{
          height: '64px',
          backgroundColor: GROWW_THEME.colors.bgSurface,
          borderBottom: `1px solid ${GROWW_THEME.colors.border}`,
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}
      >
        {/* Quick Ticker Bar - Clickable Indices */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {headerIndices.map((idxItem, i) => (
            <React.Fragment key={idxItem.name}>
              {i > 0 && <div style={{ width: '1px', height: '16px', backgroundColor: GROWW_THEME.colors.border }} />}
              <div
                onClick={() => setActiveTerminalSymbol(idxItem.name)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  transition: 'var(--transition-fast)',
                }}
                className="groww-btn-secondary"
                title={`Click to open Pro Trading Terminal for ${idxItem.name}`}
              >
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: GROWW_THEME.colors.textMuted }}>{idxItem.name}</span>
                <span style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>{idxItem.price}</span>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: idxItem.positive ? GROWW_THEME.colors.green : GROWW_THEME.colors.red }}>
                  {idxItem.change}
                </span>
                <Maximize2 size={13} color={GROWW_THEME.colors.green} style={{ opacity: 0.8 }} />
              </div>
            </React.Fragment>
          ))}
        </div>

        {/* Search & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ position: 'relative', width: '280px' }}>
            <Search size={16} color={GROWW_THEME.colors.textMuted} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search stocks (e.g. Reliance, TCS)..."
              className="groww-input"
              style={{ width: '100%', paddingLeft: '36px', height: '38px', fontSize: '0.85rem' }}
            />
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              backgroundColor: GROWW_THEME.colors.greenBg,
              border: `1px solid ${GROWW_THEME.colors.greenBorder}`,
              color: GROWW_THEME.colors.green,
              fontSize: '0.75rem',
              fontWeight: 700,
            }}
          >
            <Zap size={13} fill={GROWW_THEME.colors.green} />
            <span>MARKET OPEN</span>
          </div>

          {/* Bell Icon */}
          <button
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
            title="Notifications"
          >
            <Bell size={18} />
          </button>

          {/* Theme Toggle Button - Positioned immediately to the right of Bell Icon */}
          <button
            onClick={toggleTheme}
            style={{
              background: GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${GROWW_THEME.colors.border}`,
              color: theme === 'dark' ? '#ffb703' : '#2563eb',
              borderRadius: '50%',
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          {/* User Profile */}
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${GROWW_THEME.colors.border}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: GROWW_THEME.colors.textPrimary,
              cursor: 'pointer',
            }}
          >
            <User size={18} />
          </div>
        </div>
      </header>

      {/* Pro Trading Terminal Modal overlay when index clicked */}
      {activeTerminalSymbol && (
        <ProTradingTerminal
          symbol={activeTerminalSymbol}
          onClose={() => setActiveTerminalSymbol(null)}
        />
      )}
    </>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Bell,
  User,
  Zap,
  Sun,
  Moon,
  Maximize2,
  LogOut,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { GROWW_THEME } from '../utils/theme';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { ProTradingTerminal } from './ProTradingTerminal';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTerminalSymbol, setActiveTerminalSymbol] = useState<string | null>(null);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    if (showProfileMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showProfileMenu]);

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

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

          {/* User Profile Dropdown Container */}
          <div style={{ position: 'relative' }} ref={profileMenuRef}>
            <button
              type="button"
              onClick={() => setShowProfileMenu((prev) => !prev)}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                border: `1px solid ${showProfileMenu ? GROWW_THEME.colors.green : GROWW_THEME.colors.border}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: showProfileMenu ? GROWW_THEME.colors.green : GROWW_THEME.colors.textPrimary,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              title="Trader Account & Session"
            >
              <User size={18} />
            </button>

            {showProfileMenu && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '46px',
                  width: '260px',
                  backgroundColor: GROWW_THEME.colors.bgSurface,
                  border: `1px solid ${GROWW_THEME.colors.border}`,
                  borderRadius: '12px',
                  boxShadow: '0 12px 32px rgba(0, 0, 0, 0.4)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  zIndex: 100,
                }}
              >
                {/* User identity details */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      backgroundColor: GROWW_THEME.colors.greenBg,
                      border: `1px solid ${GROWW_THEME.colors.greenBorder}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      color: GROWW_THEME.colors.green,
                      fontSize: '0.9rem',
                    }}
                  >
                    DP
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 700, color: GROWW_THEME.colors.textPrimary }}>
                      {user?.name || 'Dinesh Pawara'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>
                      {user?.email || 'pawaradinesh45@gmail.com'}
                    </span>
                  </div>
                </div>

                {/* Status Badges */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      backgroundColor: GROWW_THEME.colors.greenBg,
                      border: `1px solid ${GROWW_THEME.colors.greenBorder}`,
                      color: GROWW_THEME.colors.green,
                      fontSize: '0.72rem',
                      fontWeight: 700,
                    }}
                  >
                    <ShieldCheck size={14} />
                    <span>AUTHORIZED MASTER TRADER</span>
                  </div>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(59, 130, 246, 0.1)',
                      border: '1px solid rgba(59, 130, 246, 0.25)',
                      color: '#3b82f6',
                      fontSize: '0.72rem',
                      fontWeight: 600,
                    }}
                  >
                    <CheckCircle2 size={13} />
                    <span>2FA Protected Session</span>
                  </div>
                </div>

                <div style={{ height: '1px', backgroundColor: GROWW_THEME.colors.border }} />

                {/* Logout Button */}
                <button
                  type="button"
                  onClick={handleLogout}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    color: '#ef4444',
                    fontSize: '0.82rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
                  }}
                >
                  <LogOut size={15} />
                  <span>Logout from Terminal</span>
                </button>
              </div>
            )}
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

export default Header;

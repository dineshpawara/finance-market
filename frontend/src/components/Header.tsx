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
  Key,
  Copy,
  Check,
  BellOff,
} from 'lucide-react';
import { GROWW_THEME } from '../utils/theme';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { ProTradingTerminal } from './ProTradingTerminal';
import {
  getPendingMasterKeyNotificationApi,
  dismissMasterKeyNotificationApi,
  type MasterKeyNotificationResponse,
} from '../api/auth';

export const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, accessToken, logout } = useAuth();
  const navigate = useNavigate();

  const [activeTerminalSymbol, setActiveTerminalSymbol] = useState<string | null>(null);

  // Profile Menu state
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  // Notifications state
  const [showNotifications, setShowNotifications] = useState(false);
  const [pendingNotification, setPendingNotification] = useState<MasterKeyNotificationResponse | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [isDismissing, setIsDismissing] = useState(false);
  const notificationMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (profileMenuRef.current && !profileMenuRef.current.contains(target)) {
        setShowProfileMenu(false);
      }
      if (notificationMenuRef.current && !notificationMenuRef.current.contains(target)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Poll for pending Master Key notifications
  useEffect(() => {
    let isMounted = true;

    const fetchNotification = async () => {
      if (!accessToken) return;
      try {
        const res = await getPendingMasterKeyNotificationApi(accessToken);
        if (isMounted) {
          if (res.has_notification) {
            setPendingNotification(res);
          } else {
            setPendingNotification(null);
          }
        }
      } catch {
        // Silently skip if network error or unauthenticated
      }
    };

    fetchNotification();
    const interval = setInterval(fetchNotification, 20000); // Check every 20s

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [accessToken]);

  // Copy key to clipboard with visual feedback
  const handleCopyKey = async () => {
    if (!pendingNotification?.master_key) return;
    try {
      await navigator.clipboard.writeText(pendingNotification.master_key);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    } catch {
      // Fallback
    }
  };

  // Dismiss notification and scrub plaintext key on backend
  const handleDismissNotification = async () => {
    if (!pendingNotification?.notification_id || !accessToken) return;
    setIsDismissing(true);
    try {
      await dismissMasterKeyNotificationApi(accessToken, pendingNotification.notification_id);
      setPendingNotification(null);
      setShowNotifications(false);
    } catch (err) {
      console.error('[Header] Failed to dismiss notification:', err);
    } finally {
      setIsDismissing(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  const headerIndices = [
    { name: 'NIFTY 50', price: '24,852.15', change: '+124.50 (0.50%)', positive: true },
    { name: 'SENSEX', price: '81,450.80', change: '+340.20 (0.42%)', positive: true },
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

          {/* Bell Icon & Notifications Dropdown */}
          <div style={{ position: 'relative' }} ref={notificationMenuRef}>
            <button
              type="button"
              onClick={() => setShowNotifications((prev) => !prev)}
              style={{
                background: GROWW_THEME.colors.bgSurfaceHover,
                border: `1px solid ${showNotifications ? GROWW_THEME.colors.green : GROWW_THEME.colors.border}`,
                color: showNotifications ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                borderRadius: '50%',
                width: '36px',
                height: '36px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                position: 'relative',
                transition: 'all 0.2s ease',
              }}
              title="Security & System Notifications"
              aria-label="Notifications"
            >
              <Bell size={18} />
              {/* Pulsing Alert Indicator if pending Master Key notification exists */}
              {pendingNotification?.has_notification && (
                <span
                  style={{
                    position: 'absolute',
                    top: '3px',
                    right: '3px',
                    width: '9px',
                    height: '9px',
                    borderRadius: '50%',
                    backgroundColor: '#ffb703',
                    border: `2px solid ${GROWW_THEME.colors.bgSurface}`,
                    boxShadow: '0 0 8px #ffb703',
                    animation: 'pulse 1.8s infinite',
                  }}
                />
              )}
            </button>

            {/* Notification Dropdown Menu */}
            {showNotifications && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '46px',
                  width: '360px',
                  backgroundColor: GROWW_THEME.colors.bgSurface,
                  border: `1px solid ${GROWW_THEME.colors.border}`,
                  borderRadius: '14px',
                  boxShadow: '0 16px 40px rgba(0, 0, 0, 0.45)',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  zIndex: 110,
                  animation: 'fadeIn 0.2s ease-out',
                }}
              >
                {/* Header Row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.92rem', fontWeight: 800, color: GROWW_THEME.colors.textPrimary }}>
                      Notifications
                    </span>
                    <span
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: '10px',
                        backgroundColor: pendingNotification?.has_notification ? 'rgba(255, 183, 3, 0.15)' : 'rgba(100, 116, 139, 0.15)',
                        color: pendingNotification?.has_notification ? '#ffb703' : GROWW_THEME.colors.textMuted,
                        border: `1px solid ${pendingNotification?.has_notification ? 'rgba(255, 183, 3, 0.3)' : 'transparent'}`,
                      }}
                    >
                      {pendingNotification?.has_notification ? '1 Security Alert' : '0 New'}
                    </span>
                  </div>
                </div>

                <div style={{ height: '1px', backgroundColor: GROWW_THEME.colors.border }} />

                {/* Notification Item: Master Key Card */}
                {pendingNotification?.has_notification ? (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '10px',
                      padding: '12px',
                      borderRadius: '10px',
                      backgroundColor: theme === 'dark' ? 'rgba(255, 183, 3, 0.05)' : '#fffdfa',
                      border: '1px solid rgba(255, 183, 3, 0.35)',
                    }}
                  >
                    {/* Title with Key icon */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div
                          style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '8px',
                            backgroundColor: 'rgba(255, 183, 3, 0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#ffb703',
                          }}
                        >
                          <Key size={15} />
                        </div>
                        <span style={{ fontSize: '0.86rem', fontWeight: 700, color: GROWW_THEME.colors.textPrimary }}>
                          New Master Security Key
                        </span>
                      </div>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: 'rgba(255, 183, 3, 0.2)',
                          color: '#ffb703',
                        }}
                      >
                        CONFIDENTIAL
                      </span>
                    </div>

                    <p style={{ fontSize: '0.76rem', color: GROWW_THEME.colors.textSecondary, margin: 0, lineHeight: 1.45 }}>
                      Generated after your recent password reset. Store this in your password manager immediately.
                    </p>

                    {/* Master Key Box with 1-Click Copy */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: '8px',
                        backgroundColor: theme === 'dark' ? 'rgba(0, 0, 0, 0.5)' : '#f1f5f9',
                        border: `1px solid ${GROWW_THEME.colors.border}`,
                      }}
                    >
                      <span
                        style={{
                          fontFamily: 'monospace',
                          fontSize: '0.96rem',
                          fontWeight: 700,
                          letterSpacing: '0.06em',
                          color: GROWW_THEME.colors.green,
                        }}
                      >
                        {pendingNotification.master_key}
                      </span>

                      <button
                        type="button"
                        onClick={handleCopyKey}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '5px 10px',
                          borderRadius: '6px',
                          backgroundColor: copiedKey ? 'rgba(0, 208, 156, 0.2)' : GROWW_THEME.colors.bgSurfaceHover,
                          border: `1px solid ${copiedKey ? GROWW_THEME.colors.green : GROWW_THEME.colors.border}`,
                          color: copiedKey ? GROWW_THEME.colors.green : GROWW_THEME.colors.textPrimary,
                          fontSize: '0.74rem',
                          fontWeight: 700,
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                        title="Copy Master Key to Clipboard"
                      >
                        {copiedKey ? <Check size={13} /> : <Copy size={13} />}
                        <span>{copiedKey ? 'Copied! ✓' : 'Copy Key'}</span>
                      </button>
                    </div>

                    {/* Dismiss Button */}
                    <button
                      type="button"
                      onClick={handleDismissNotification}
                      disabled={isDismissing}
                      style={{
                        marginTop: '2px',
                        width: '100%',
                        padding: '8px 12px',
                        borderRadius: '8px',
                        backgroundColor: 'transparent',
                        border: `1px solid ${GROWW_THEME.colors.border}`,
                        color: GROWW_THEME.colors.textSecondary,
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        cursor: isDismissing ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = GROWW_THEME.colors.green;
                        e.currentTarget.style.color = GROWW_THEME.colors.green;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = GROWW_THEME.colors.border;
                        e.currentTarget.style.color = GROWW_THEME.colors.textSecondary;
                      }}
                    >
                      <CheckCircle2 size={14} />
                      <span>{isDismissing ? 'Dismissing & Scrubbing...' : 'I Have Saved This Key (Dismiss)'}</span>
                    </button>

                    <span style={{ fontSize: '0.68rem', color: GROWW_THEME.colors.textMuted, textAlign: 'center' }}>
                      Security Notice: Dismissing permanently removes plaintext key from view.
                    </span>
                  </div>
                ) : (
                  /* Empty State */
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '24px 12px',
                      textAlign: 'center',
                      gap: '8px',
                    }}
                  >
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '50%',
                        backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: GROWW_THEME.colors.textMuted,
                      }}
                    >
                      <BellOff size={20} />
                    </div>
                    <span style={{ fontSize: '0.86rem', fontWeight: 700, color: GROWW_THEME.colors.textPrimary }}>
                      No new notifications
                    </span>
                    <span style={{ fontSize: '0.75rem', color: GROWW_THEME.colors.textMuted }}>
                      Terminal security notices and key rotations will appear here.
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

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
                      {user?.email || 'admin@finance.market'}
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

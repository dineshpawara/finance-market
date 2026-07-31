import React from 'react';
import { 
  LayoutDashboard, 
  TrendingUp, 
  TableProperties, 
  Newspaper, 
  Bookmark, 
  ChevronLeft, 
  ChevronRight
} from 'lucide-react';
import { GROWW_THEME } from '../utils/theme';

export type TabType = 'dashboard' | 'option-chain' | 'nifty50' | 'news' | 'watchlist';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  width: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  isCollapsed,
  onToggleCollapse,
  width,
}) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: 'LIVE' },
    { id: 'option-chain', label: 'Option Chain', icon: TableProperties },
    { id: 'nifty50', label: 'Nifty 50 Stocks', icon: TrendingUp, badge: '50' },
    { id: 'news', label: 'Market News', icon: Newspaper },
    { id: 'watchlist', label: 'Watchlist', icon: Bookmark },
  ];

  return (
    <aside
      style={{
        width: `${width}px`,
        transition: 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        backgroundColor: GROWW_THEME.colors.bgSurface,
        borderRight: `1px solid ${GROWW_THEME.colors.border}`,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'relative',
        zIndex: 50,
        userSelect: 'none',
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: isCollapsed ? '20px 12px' : '20px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          borderBottom: `1px solid ${GROWW_THEME.colors.border}`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              backgroundColor: GROWW_THEME.colors.green,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: GROWW_THEME.colors.greenBg,
            }}
          >
            <TrendingUp size={22} color="#ffffff" strokeWidth={2.5} />
          </div>
          {!isCollapsed && (
            <div>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 800, lineHeight: 1.1, letterSpacing: '-0.03em' }}>
                GROWW<span style={{ color: GROWW_THEME.colors.green }}>.IN</span>
              </h2>
              <span style={{ fontSize: '0.7rem', color: GROWW_THEME.colors.textMuted, fontWeight: 500 }}>
                MARKET TERMINAL
              </span>
            </div>
          )}
        </div>

        {!isCollapsed && (
          <button
            onClick={onToggleCollapse}
            style={{
              background: GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${GROWW_THEME.colors.border}`,
              color: GROWW_THEME.colors.textSecondary,
              borderRadius: '6px',
              width: '28px',
              height: '28px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
            title="Collapse Sidebar"
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <nav style={{ flex: 1, padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {menuItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id as TabType)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: isCollapsed ? 'center' : 'space-between',
                padding: isCollapsed ? '12px' : '12px 14px',
                borderRadius: '8px',
                border: isActive ? `1px solid ${GROWW_THEME.colors.greenBorder}` : '1px solid transparent',
                backgroundColor: isActive ? GROWW_THEME.colors.greenBg : 'transparent',
                color: isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textAlign: 'left',
                width: '100%',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.92rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={20} color={isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.textSecondary} />
                {!isCollapsed && <span>{item.label}</span>}
              </div>

              {!isCollapsed && item.badge && (
                <span
                  style={{
                    fontSize: '0.68rem',
                    padding: '2px 7px',
                    borderRadius: '999px',
                    backgroundColor: isActive ? GROWW_THEME.colors.green : GROWW_THEME.colors.bgSurfaceHover,
                    color: isActive ? '#ffffff' : GROWW_THEME.colors.textMuted,
                    fontWeight: 700,
                  }}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Footer & Expand toggle */}
      {isCollapsed && (
        <div style={{ padding: '12px', borderTop: `1px solid ${GROWW_THEME.colors.border}`, display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={onToggleCollapse}
            style={{
              background: GROWW_THEME.colors.bgSurfaceHover,
              border: `1px solid ${GROWW_THEME.colors.border}`,
              color: GROWW_THEME.colors.textSecondary,
              borderRadius: '6px',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
            title="Expand Sidebar"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {!isCollapsed && (
        <div style={{ padding: '16px 20px', borderTop: `1px solid ${GROWW_THEME.colors.border}` }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: GROWW_THEME.colors.green, display: 'inline-block' }}></span>
            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: GROWW_THEME.colors.textPrimary }}>NSE / BSE LIVE</span>
          </div>
          <span style={{ fontSize: '0.7rem', color: GROWW_THEME.colors.textMuted }}>Data feed connected</span>
        </div>
      )}
    </aside>
  );
};

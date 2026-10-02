import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import { GROWW_THEME } from '../utils/theme';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Navigate to /app on authentication submission
    navigate('/app');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        backgroundColor: GROWW_THEME.colors.bgMain,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
    >
      <div
        className="groww-card"
        style={{
          width: '100%',
          maxWidth: '440px',
          padding: '36px 32px',
          boxShadow: 'var(--shadow-card)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        {/* Brand Header */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              backgroundColor: GROWW_THEME.colors.green,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '12px',
              boxShadow: GROWW_THEME.colors.greenBg,
            }}
          >
            <TrendingUp size={28} color="#ffffff" strokeWidth={2.5} />
          </div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.03em', textAlign: 'center' }}>
            GROWW<span style={{ color: GROWW_THEME.colors.green }}>.IN</span>
          </h1>
          <p style={{ fontSize: '0.85rem', color: GROWW_THEME.colors.textMuted, marginTop: '4px', textAlign: 'center' }}>
            {isLogin ? 'Log in to your Market Terminal account' : 'Create a new Groww account'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div
          style={{
            display: 'flex',
            backgroundColor: GROWW_THEME.colors.bgSurfaceHover,
            padding: '4px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '24px',
            border: `1px solid ${GROWW_THEME.colors.border}`,
          }}
        >
          <button
            onClick={() => setIsLogin(true)}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: isLogin ? GROWW_THEME.colors.bgSurface : 'transparent',
              color: isLogin ? GROWW_THEME.colors.textPrimary : GROWW_THEME.colors.textMuted,
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'var(--transition-fast)',
            }}
          >
            Log In
          </button>
          <button
            onClick={() => setIsLogin(false)}
            style={{
              flex: 1,
              padding: '8px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              backgroundColor: !isLogin ? GROWW_THEME.colors.bgSurface : 'transparent',
              color: !isLogin ? GROWW_THEME.colors.textPrimary : GROWW_THEME.colors.textMuted,
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'var(--transition-fast)',
            }}
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: GROWW_THEME.colors.textSecondary, marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={16} color={GROWW_THEME.colors.textMuted} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email"
                required
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="groww-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: GROWW_THEME.colors.textSecondary, marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color={GROWW_THEME.colors.textMuted} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="groww-input"
                style={{ width: '100%', paddingLeft: '38px', height: '42px' }}
              />
            </div>
          </div>

          <button
            type="submit"
            className="groww-btn groww-btn-primary"
            style={{ width: '100%', height: '44px', marginTop: '8px', fontSize: '0.95rem' }}
          >
            <span>{isLogin ? 'Log In to Terminal' : 'Create Account'}</span>
            <ArrowRight size={18} />
          </button>
        </form>

        {/* Quick Bypass Button */}
        <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: `1px solid ${GROWW_THEME.colors.border}`, textAlign: 'center' }}>
          <button
            onClick={() => navigate('/app')}
            style={{
              background: 'none',
              border: 'none',
              color: GROWW_THEME.colors.green,
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <ShieldCheck size={16} />
            <span>Open Terminal Direct (/app)</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;

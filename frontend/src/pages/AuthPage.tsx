import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Lock, Eye, EyeOff, ArrowRight, Sun, Moon, CheckCircle2, AlertCircle } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { MarketBackground } from '../components/MarketBackground';
import { ForgotPasswordView } from '../components/ForgotPasswordView';
import { TotpVerificationView } from '../components/TotpVerificationView';

export const AuthPage: React.FC = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { loginWithPassword, isAuthenticated } = useAuth();
  const isDark = theme === 'dark';

  // Auth View State: 'login' | 'forgot-password' | 'totp'
  const [authView, setAuthView] = useState<'login' | 'forgot-password' | 'totp'>('login');

  // Login Form States
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [tempToken, setTempToken] = useState<string | null>(null);
  const [resetSuccessToast, setResetSuccessToast] = useState(false);

  // Auto-redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Financial Motivation Mindset Quote
  const motivationalQuote =
    '“The stock market is a device for transferring money from the impatient to the patient.” — Discipline & conviction define every winning trade.';

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    setIsLoading(true);

    try {
      const res = await loginWithPassword(password);
      if (res.requires_2fa && res.temp_token) {
        setTempToken(res.temp_token);
        setAuthView('totp');
      } else if (res.access_token) {
        navigate('/app', { replace: true });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid terminal credentials. Please try again.';
      setLoginError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordResetSuccess = () => {
    setAuthView('login');
    setResetSuccessToast(true);
    setTimeout(() => {
      setResetSuccessToast(false);
    }, 4000);
  };

  return (
    <div className="auth-viewport">
      {/* Dynamic Candlestick & Market Visual Background */}
      <MarketBackground />

      {/* Top Floating Theme Toggle Bar */}
      <div className="auth-theme-bar">
        <button
          onClick={toggleTheme}
          className="auth-theme-toggle-btn"
          title={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
        >
          {isDark ? (
            <>
              <Sun size={16} color="#ffb703" />
              <span>Light Mode</span>
            </>
          ) : (
            <>
              <Moon size={16} color="#2563eb" />
              <span>Dark Mode</span>
            </>
          )}
        </button>
      </div>

      {/* Central Glassmorphic Auth Card */}
      <div className="auth-card">
        {/* Reset Success Toast */}
        {resetSuccessToast && (
          <div className="auth-toast-success">
            <CheckCircle2 size={18} />
            <span>Master credentials updated successfully! You can now log in.</span>
          </div>
        )}

        {/* View Switch: Login vs Forgot Password vs TOTP 2FA */}
        {authView === 'login' && (
          <div>
            {/* Header: TrendingUp Symbol Badge */}
            <div className="auth-header">
              <div className="auth-logo-badge">
                <TrendingUp size={32} color="#ffffff" strokeWidth={2.6} />
              </div>

              {/* Financial Motivation Text / Description */}
              <p className="auth-quote">
                {motivationalQuote}
              </p>

              {/* Single User Name in Heading 1 Bold */}
              <h1 className="auth-user-name">
                Dinesh Pawara
              </h1>

              {/* Verified Single User Status Badge */}
              <div className="auth-trader-badge">
                <span className="auth-trader-dot" />
                <span>AUTHORIZED MASTER TRADER</span>
              </div>
            </div>

            {/* Login Error Banner */}
            {loginError && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  fontSize: '0.85rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{loginError}</span>
              </div>
            )}

            {/* Login Form: Single Password Field Matching New Structure */}
            <form onSubmit={handleLoginSubmit} className="auth-form">
              <div>
                <label htmlFor="terminal-password" className="auth-field-label">
                  Password
                </label>
                <div className="auth-input-wrapper">
                  <Lock size={17} className="auth-input-icon-left" />
                  <input
                    id="terminal-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoFocus
                    placeholder="Enter terminal password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="groww-input auth-input-control"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="auth-input-btn-right"
                  >
                    {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="groww-btn groww-btn-primary auth-submit-btn"
              >
                <span>{isLoading ? 'Verifying Password...' : 'Verify & Continue to 2FA'}</span>
                <ArrowRight size={18} />
              </button>

              {/* Forgot Password Link - In-place Toggle without Reload or Route change */}
              <div className="auth-forgot-link-wrapper">
                <button
                  type="button"
                  onClick={() => setAuthView('forgot-password')}
                  className="auth-forgot-link"
                >
                  Forgot Password?
                </button>
              </div>
            </form>
          </div>
        )}

        {/* View 2: Forgot Password Workflow */}
        {authView === 'forgot-password' && (
          <ForgotPasswordView
            onBackToLogin={() => setAuthView('login')}
            onPasswordResetSuccess={handlePasswordResetSuccess}
          />
        )}

        {/* View 3: TOTP Google Authenticator Workflow */}
        {authView === 'totp' && (
          <TotpVerificationView
            onBackToLogin={() => setAuthView('login')}
            tempToken={tempToken}
          />
        )}
      </div>
    </div>
  );
};

export default AuthPage;

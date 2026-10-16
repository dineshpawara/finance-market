import React, { useState } from 'react';
import {
  TrendingUp,
  Key,
  Lock,
  Eye,
  EyeOff,
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Clock,
  RotateCcw,
} from 'lucide-react';
import {
  verifyMasterKeyApi,
  resetPasswordWithKeyApi,
  AuthApiError,
} from '../api/auth';

interface ForgotPasswordViewProps {
  onBackToLogin: () => void;
  onPasswordResetSuccess: () => void;
}

// Master Key regex: 4 blocks of 4 alphanumeric uppercase characters
const MASTER_KEY_REGEX = /^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;

export const ForgotPasswordView: React.FC<ForgotPasswordViewProps> = ({
  onBackToLogin,
  onPasswordResetSuccess,
}) => {
  // Step 1: 'verify-key' | Step 2: 'reset-password' | Step 3: 'success'
  const [step, setStep] = useState<'verify-key' | 'reset-password' | 'success'>('verify-key');

  // Input states
  const [masterKey, setMasterKey] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Security token state (received from Stage 1 verify)
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [tokenExpiresIn, setTokenExpiresIn] = useState<number | null>(null);

  // Visibility toggles
  const [showMasterKey, setShowMasterKey] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Status & loading
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [warningMsg, setWarningMsg] = useState<string | null>(null);
  const [sessionExpired, setSessionExpired] = useState(false);

  // Auto-format master key helper: converts to uppercase and inserts dashes
  const handleMasterKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    setWarningMsg(null);

    // Clean input: uppercase alphanumeric and hyphen only
    const raw = e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, '');

    // Auto-dash formatting if user types continuous alphanumeric string
    const cleanChars = raw.replace(/-/g, '').slice(0, 16);
    const parts: string[] = [];
    for (let i = 0; i < cleanChars.length; i += 4) {
      parts.push(cleanChars.slice(i, i + 4));
    }
    const formatted = parts.join('-');

    setMasterKey(formatted);
  };

  // Step 1: Verify Master Key via Backend API
  const handleVerifyMasterKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setWarningMsg(null);

    const trimmedKey = masterKey.trim();

    if (!trimmedKey) {
      setErrorMsg('Please enter your Master Security Key.');
      return;
    }

    if (!MASTER_KEY_REGEX.test(trimmedKey)) {
      setErrorMsg('Master Key must be in the format: XXXX-XXXX-XXXX-XXXX (e.g. ABCD-1234-EFGH-5678)');
      return;
    }

    setIsLoading(true);

    try {
      const response = await verifyMasterKeyApi({ master_key: trimmedKey });

      if (response.success && response.reset_token) {
        setResetToken(response.reset_token);
        setTokenExpiresIn(response.expires_in || 900);
        setSessionExpired(false);
        setStep('reset-password');
      } else {
        setErrorMsg(response.message || 'Verification could not be completed. Please try again.');
      }
    } catch (err: unknown) {
      if (err instanceof AuthApiError) {
        if (err.statusCode === 429) {
          setErrorMsg(err.message || 'Rate limit exceeded. Too many attempts. Please wait 15 minutes before retrying.');
        } else if (err.statusCode === 401) {
          setErrorMsg(err.message || 'Invalid Master Security Key. Please verify and re-enter.');
        } else if (err.statusCode === 422) {
          setErrorMsg('Invalid Master Key format. Expected 4 blocks of 4 alphanumeric characters.');
        } else {
          setErrorMsg(err.message || 'Master Key verification failed. Please try again.');
        }
      } else {
        setErrorMsg('Unable to connect to authentication server. Please verify your connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Step 2: Reset Password via Backend API
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setWarningMsg(null);

    if (!resetToken) {
      setErrorMsg('Verification session missing or expired. Please verify your Master Key again.');
      setSessionExpired(true);
      return;
    }

    if (!newPassword) {
      setErrorMsg('Please enter a new password.');
      return;
    }

    if (newPassword.length < 6) {
      setErrorMsg('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMsg('New password and Confirm password do not match.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await resetPasswordWithKeyApi({
        reset_token: resetToken,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      if (response.success) {
        setStep('success');
        // Clear sensitive token from state
        setResetToken(null);
      } else {
        setErrorMsg(response.message || 'Password update failed. Please try again.');
      }
    } catch (err: unknown) {
      if (err instanceof AuthApiError) {
        if (err.statusCode === 401) {
          setErrorMsg('Your reset session has expired (15-minute window). Please verify your Master Key again.');
          setSessionExpired(true);
        } else if (err.statusCode === 400 && err.code === 'BAD_REQUEST') {
          // Password history or business error
          setErrorMsg(err.message || 'New password cannot be the same as any of your recently used passwords.');
        } else if (err.statusCode === 429) {
          setErrorMsg('Too many reset attempts. Please slow down and try again shortly.');
        } else {
          setErrorMsg(err.message || 'Failed to update password. Please ensure requirements are met.');
        }
      } else {
        setErrorMsg('Network error while resetting password. Please check your connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Restart recovery flow if session expired
  const handleRestartFlow = () => {
    setResetToken(null);
    setSessionExpired(false);
    setErrorMsg(null);
    setWarningMsg(null);
    setNewPassword('');
    setConfirmPassword('');
    setStep('verify-key');
  };

  return (
    <div className="forgot-container">
      {/* Brand & Symbol Header with TrendingUp */}
      <div className="forgot-header">
        <div className="forgot-logo-badge">
          <TrendingUp size={30} color="#ffffff" strokeWidth={2.5} />
        </div>

        <h2 className="forgot-title">
          {step === 'verify-key' && 'Master Key Verification'}
          {step === 'reset-password' && 'Set New Password'}
          {step === 'success' && 'Password Updated!'}
        </h2>

        <p className="forgot-desc">
          {step === 'verify-key' &&
            'Enter your single-user master security authorization key to reset your terminal credentials.'}
          {step === 'reset-password' &&
            'Master key verified. Choose a strong new password for your terminal access.'}
          {step === 'success' &&
            'Your security credentials have been updated. You can now log in.'}
        </p>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="forgot-error-banner" role="alert">
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Warning Alert Banner (e.g., remaining attempts or session notice) */}
      {warningMsg && (
        <div
          className="forgot-error-banner"
          style={{
            backgroundColor: 'rgba(255, 183, 3, 0.12)',
            borderColor: 'rgba(255, 183, 3, 0.4)',
            color: '#ffb703',
          }}
          role="status"
        >
          <AlertTriangle size={16} style={{ flexShrink: 0 }} />
          <span>{warningMsg}</span>
        </div>
      )}

      {/* STEP 1: Verify Master Key */}
      {step === 'verify-key' && (
        <form onSubmit={handleVerifyMasterKey} className="forgot-form" noValidate>
          <div>
            <label htmlFor="master-key-input" className="forgot-field-label">
              Master Security Key
            </label>
            <div className="auth-input-wrapper">
              <Key size={16} className="auth-input-icon-left" />
              <input
                id="master-key-input"
                type={showMasterKey ? 'text' : 'password'}
                required
                autoFocus
                autoComplete="off"
                spellCheck="false"
                maxLength={19}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                value={masterKey}
                onChange={handleMasterKeyChange}
                className="groww-input forgot-input-control forgot-key-input"
                style={{ letterSpacing: '0.08em', fontWeight: 600 }}
              />
              <button
                type="button"
                onClick={() => setShowMasterKey(!showMasterKey)}
                aria-label={showMasterKey ? 'Hide master key' : 'Show master key'}
                className="auth-input-btn-right"
              >
                {showMasterKey ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '6px',
              }}
            >
              <span className="forgot-helper-note">
                Format: 16 alphanumeric characters separated by dashes.
              </span>
              <span
                style={{
                  fontSize: '0.72rem',
                  color: masterKey.length === 19 ? 'var(--groww-green)' : 'var(--text-muted)',
                  fontFamily: 'monospace',
                  fontWeight: 600,
                }}
              >
                {masterKey.length}/19
              </span>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || masterKey.length < 19}
            className="groww-btn groww-btn-primary forgot-submit-btn"
          >
            {isLoading ? (
              <span>Verifying Master Key...</span>
            ) : (
              <>
                <ShieldCheck size={18} />
                <span>Verify Master Key</span>
              </>
            )}
          </button>
        </form>
      )}

      {/* STEP 2: New Password & Confirm Password */}
      {step === 'reset-password' && (
        <form onSubmit={handleResetPassword} className="forgot-form">
          {/* Master Key Verified Status Badge */}
          <div className="forgot-verified-badge">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle2 size={16} />
              <span>Master Key Verified</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={13} style={{ opacity: 0.8 }} />
              <span style={{ fontSize: '0.72rem', opacity: 0.9, fontFamily: 'monospace' }}>
                Valid for {tokenExpiresIn ? Math.floor(tokenExpiresIn / 60) : 15}m
              </span>
            </div>
          </div>

          {/* Session Expired Reset Prompt */}
          {sessionExpired && (
            <div style={{ textAlign: 'center', margin: '4px 0' }}>
              <button
                type="button"
                onClick={handleRestartFlow}
                className="forgot-back-btn"
                style={{ color: 'var(--groww-green)', gap: '6px' }}
              >
                <RotateCcw size={14} />
                <span>Click here to re-verify your Master Key</span>
              </button>
            </div>
          )}

          {/* New Password Field */}
          <div>
            <label htmlFor="new-password-input" className="forgot-field-label">
              New Password
            </label>
            <div className="auth-input-wrapper">
              <Lock size={16} className="auth-input-icon-left" />
              <input
                id="new-password-input"
                type={showNewPassword ? 'text' : 'password'}
                required
                autoFocus
                autoComplete="new-password"
                placeholder="Enter new password (min. 6 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="groww-input forgot-input-control"
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                aria-label={showNewPassword ? 'Hide new password' : 'Show new password'}
                className="auth-input-btn-right"
              >
                {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm Password Field */}
          <div>
            <label htmlFor="confirm-password-input" className="forgot-field-label">
              Confirm Password
            </label>
            <div className="auth-input-wrapper">
              <Lock size={16} className="auth-input-icon-left" />
              <input
                id="confirm-password-input"
                type={showConfirmPassword ? 'text' : 'password'}
                required
                autoComplete="new-password"
                placeholder="Re-enter new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="groww-input forgot-input-control"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                className="auth-input-btn-right"
              >
                {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {confirmPassword && newPassword !== confirmPassword && (
              <span className="forgot-match-indicator error">
                Passwords do not match
              </span>
            )}
            {confirmPassword && newPassword === confirmPassword && (
              <span className="forgot-match-indicator success">
                Passwords match ✓
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || sessionExpired || !newPassword || newPassword !== confirmPassword}
            className="groww-btn groww-btn-primary forgot-submit-btn"
          >
            {isLoading ? <span>Updating Password...</span> : <span>Save New Password</span>}
          </button>
        </form>
      )}

      {/* STEP 3: Success Confirmation */}
      {step === 'success' && (
        <div className="forgot-success-box">
          <div className="forgot-success-icon-wrap">
            <CheckCircle2 size={32} />
          </div>
          <span className="forgot-success-title">
            Password Reset Successfully
          </span>
          <p className="forgot-success-desc">
            Your credentials have been securely updated. You can now log into your terminal account.
          </p>
          <button
            onClick={onPasswordResetSuccess}
            className="groww-btn groww-btn-primary"
            style={{ width: '100%', height: '44px', borderRadius: '12px' }}
          >
            Proceed to Login
          </button>
        </div>
      )}

      {/* Back to Login Button */}
      {step !== 'success' && (
        <div className="forgot-back-wrapper">
          <button onClick={onBackToLogin} className="forgot-back-btn">
            <ArrowLeft size={16} />
            <span>Back to Login</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ForgotPasswordView;

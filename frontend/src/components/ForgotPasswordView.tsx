import React, { useState } from 'react';
import { TrendingUp, Key, Lock, Eye, EyeOff, ArrowLeft, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';

interface ForgotPasswordViewProps {
  onBackToLogin: () => void;
  onPasswordResetSuccess: () => void;
}

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

  // Visibility toggles
  const [showMasterKey, setShowMasterKey] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Status & loading
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Step 1: Verify Master Key
  const handleVerifyMasterKey = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!masterKey.trim()) {
      setErrorMsg('Please enter your Master Security Key');
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      if (masterKey.trim().length < 4) {
        setErrorMsg('Master Security Key must be at least 4 characters');
        return;
      }
      setStep('reset-password');
    }, 700);
  };

  // Step 2: Reset Password
  const handleResetPassword = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!newPassword) {
      setErrorMsg('Please enter a new password');
      return;
    }
    if (newPassword.length < 6) {
      setErrorMsg('Password should be at least 6 characters long');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('New password and Confirm password do not match');
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setStep('success');
      setTimeout(() => {
        onPasswordResetSuccess();
      }, 1600);
    }, 800);
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
            'Your security credentials have been updated. Redirecting to terminal login...'}
        </p>
      </div>

      {/* Error Alert Banner */}
      {errorMsg && (
        <div className="forgot-error-banner">
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* STEP 1: Verify Master Key ONLY */}
      {step === 'verify-key' && (
        <form onSubmit={handleVerifyMasterKey} className="forgot-form">
          <div>
            <label htmlFor="master-key-input" className="forgot-field-label">
              Master Key
            </label>
            <div className="auth-input-wrapper">
              <Key size={16} className="auth-input-icon-left" />
              <input
                id="master-key-input"
                type={showMasterKey ? 'text' : 'password'}
                required
                autoFocus
                placeholder="Enter authorized Master Key..."
                value={masterKey}
                onChange={(e) => setMasterKey(e.target.value)}
                className="groww-input forgot-input-control forgot-key-input"
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
            <span className="forgot-helper-note">
              Security Note: Only Dinesh Pawara’s master key can authorize this reset.
            </span>
          </div>

          <button
            type="submit"
            disabled={isLoading}
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
            <span style={{ fontSize: '0.72rem', opacity: 0.8, fontFamily: 'monospace' }}>
              AUTH-OK
            </span>
          </div>

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
                placeholder="Enter new password"
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
            disabled={isLoading}
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
            You can now log in using your new credentials.
          </p>
          <button
            onClick={onPasswordResetSuccess}
            className="groww-btn groww-btn-primary"
            style={{ width: '100%', height: '42px', borderRadius: '10px' }}
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

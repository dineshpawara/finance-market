/**
 * Centralized Authentication & 2FA API Endpoints
 * ==============================================
 * Targets FastAPI V1 authentication and Google Authenticator TOTP services.
 */

export const BASE_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const AUTH_ENDPOINTS = {
  // Stage 1: Primary password authentication (returns JWT or 2FA challenge)
  LOGIN: `${BASE_API_URL}/auth/login`,

  // Stage 2: Google Authenticator TOTP passcode verification (validates temp_token + 6 digits)
  VERIFY_2FA: `${BASE_API_URL}/auth/2fa/verify`,

  // 2FA Lifecycle Management (requires authenticated Bearer token)
  SETUP_2FA: `${BASE_API_URL}/2fa/setup`,
  VERIFY_SETUP_2FA: `${BASE_API_URL}/2fa/verify-setup`,
  STATUS_2FA: `${BASE_API_URL}/2fa/status`,
  DISABLE_2FA: `${BASE_API_URL}/2fa/disable`,

  // Master Key 2-Stage Password Recovery Endpoints
  VERIFY_MASTER_KEY: `${BASE_API_URL}/auth/master-key/verify`,
  RESET_PASSWORD_WITH_KEY: `${BASE_API_URL}/auth/master-key/reset-password`,

  // Master Key In-App Rotation Notifications
  MASTER_KEY_NOTIFICATION: `${BASE_API_URL}/auth/master-key/notification`,
  DISMISS_MASTER_KEY_NOTIFICATION: `${BASE_API_URL}/auth/master-key/notification/dismiss`,
};
/**
 * Authentication & 2FA API Communication Layer
 * ============================================
 * Provides typed, robust HTTP communication with FastAPI authentication services.
 * Handles single-admin credentials, 2FA challenge tokens, master keys, and structured error responses.
 */

import { AUTH_ENDPOINTS } from '../endpoints/auth.endpoints';

export interface UserSummary {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
}

export interface LoginResponse {
  requires_2fa: boolean;
  temp_token: string | null;
  access_token: string | null;
  token_type?: string;
  expires_in?: number;
  user?: UserSummary | null;
}

export interface TwoFactorSetupResponse {
  secret_key: string;
  otpauth_url: string;
  qr_code_base64: string;
  status: string;
}

export interface TwoFactorVerifySetupResponse {
  success: boolean;
  message: string;
  is_enabled: boolean;
}

export interface TwoFactorStatusResponse {
  is_enabled: boolean;
  status: string;
  enabled_at: string | null;
}

export interface MasterKeyVerifyRequest {
  master_key: string;
  email?: string;
}

export interface MasterKeyVerifyResponse {
  success: boolean;
  message: string;
  reset_token: string;
  expires_in: number;
}

export interface PasswordResetWithKeyRequest {
  reset_token: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetWithKeyResponse {
  success: boolean;
  message: string;
  user_id?: string;
}

export interface MasterKeyNotificationResponse {
  has_notification: boolean;
  notification_id?: string | null;
  master_key?: string | null;
  title?: string | null;
  message?: string | null;
  created_at?: string | null;
}

export interface DismissNotificationResponse {
  success: boolean;
  message: string;
}

export class AuthApiError extends Error {
  code: string;
  statusCode: number;
  details?: unknown;

  constructor(message: string, code: string = 'AUTH_ERROR', statusCode: number = 400, details?: unknown) {
    super(message);
    this.name = 'AuthApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

/**
 * Parses JSON error from FastAPI response or returns standard message
 */
async function parseErrorResponse(res: Response): Promise<AuthApiError> {
  try {
    const errorBody = await res.json();

    // Standard enterprise error format: { error: { message, code, details } }
    if (errorBody && errorBody.error && errorBody.error.message) {
      return new AuthApiError(
        errorBody.error.message,
        errorBody.error.code || 'BAD_REQUEST',
        res.status,
        errorBody.error.details
      );
    }

    // FastAPI / Pydantic validation error format: { detail: [...] } or { detail: "..." }
    if (errorBody && errorBody.detail) {
      if (Array.isArray(errorBody.detail)) {
        const errorMsgs = errorBody.detail.map((err: { loc?: unknown[]; msg?: string }) => {
          const loc = Array.isArray(err.loc)
            ? err.loc.filter((p: unknown) => p !== 'body').join('.')
            : '';
          const msg = err.msg || 'Invalid field';
          return loc ? `${loc}: ${msg}` : msg;
        });
        return new AuthApiError(
          errorMsgs.join('; ') || 'Validation error',
          'VALIDATION_ERROR',
          res.status,
          errorBody.detail
        );
      }
      if (typeof errorBody.detail === 'string') {
        return new AuthApiError(errorBody.detail, 'BAD_REQUEST', res.status);
      }
    }
  } catch {
    // Non-JSON response
  }

  if (res.status === 429) {
    return new AuthApiError('Too many requests. Please slow down and try again after a minute.', 'RATE_LIMIT_EXCEEDED', 429);
  }
  if (res.status === 401) {
    return new AuthApiError('Authentication failed. Please verify your credentials.', 'UNAUTHORIZED', 401);
  }
  if (res.status === 423) {
    return new AuthApiError('Account is temporarily locked. Please retry later.', 'ACCOUNT_LOCKED', 423);
  }
  if (res.status === 422) {
    return new AuthApiError('Invalid request format or missing parameters (422).', 'VALIDATION_ERROR', 422);
  }

  return new AuthApiError(`Server error (${res.status}). Please try again.`, 'SERVER_ERROR', res.status);
}

/**
 * Stage 1: Authenticate with terminal password
 * Note: Single-admin terminal passes only password; backend controller defaults email from .env
 */
export async function loginApi(password: string): Promise<LoginResponse> {
  const res = await fetch(AUTH_ENDPOINTS.LOGIN, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({ password }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Stage 2: Validate 6-digit Google Authenticator passcode against temporary pre-auth token
 */
export async function verify2FaLoginApi(tempToken: string, code: string): Promise<LoginResponse> {
  const res = await fetch(AUTH_ENDPOINTS.VERIFY_2FA, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      temp_token: tempToken,
      code: code.trim(),
    }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Fetches Google Authenticator 2FA setup credentials (Secret seed & QR Code Base64)
 */
export async function setup2FaApi(token: string): Promise<TwoFactorSetupResponse> {
  const res = await fetch(AUTH_ENDPOINTS.SETUP_2FA, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Confirms initial 2FA setup by submitting first passcode generated by app
 */
export async function verifySetup2FaApi(token: string, code: string): Promise<TwoFactorVerifySetupResponse> {
  const res = await fetch(AUTH_ENDPOINTS.VERIFY_SETUP_2FA, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ code: code.trim() }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Inspects whether 2FA is currently active for the authenticated user
 */
export async function get2FaStatusApi(token: string): Promise<TwoFactorStatusResponse> {
  const res = await fetch(AUTH_ENDPOINTS.STATUS_2FA, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Deactivates 2FA upon dual verification of password and current TOTP code
 */
export async function disable2FaApi(token: string, password: string, code: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(AUTH_ENDPOINTS.DISABLE_2FA, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ password, code: code.trim() }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Stage 1: Verify Master Security Key to obtain single-use reset token
 */
export async function verifyMasterKeyApi(req: MasterKeyVerifyRequest): Promise<MasterKeyVerifyResponse> {
  const res = await fetch(AUTH_ENDPOINTS.VERIFY_MASTER_KEY, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      master_key: req.master_key.trim(),
      ...(req.email ? { email: req.email.trim() } : {}),
    }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Stage 2: Reset password using the single-use reset token
 */
export async function resetPasswordWithKeyApi(req: PasswordResetWithKeyRequest): Promise<PasswordResetWithKeyResponse> {
  const res = await fetch(AUTH_ENDPOINTS.RESET_PASSWORD_WITH_KEY, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      reset_token: req.reset_token,
      new_password: req.new_password,
      confirm_password: req.confirm_password,
    }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Fetches active unacknowledged Master Key rotation notification (for Bell icon)
 */
export async function getPendingMasterKeyNotificationApi(accessToken: string): Promise<MasterKeyNotificationResponse> {
  const res = await fetch(AUTH_ENDPOINTS.MASTER_KEY_NOTIFICATION, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}

/**
 * Dismisses the Master Key notification and requests server-side plaintext scrubbing
 */
export async function dismissMasterKeyNotificationApi(accessToken: string, notificationId: string): Promise<DismissNotificationResponse> {
  const res = await fetch(AUTH_ENDPOINTS.DISMISS_MASTER_KEY_NOTIFICATION, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ notification_id: notificationId }),
  });

  if (!res.ok) {
    throw await parseErrorResponse(res);
  }

  return res.json();
}
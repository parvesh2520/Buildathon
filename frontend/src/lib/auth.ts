const SUPABASE_URL =
  import.meta.env.VITE_SUPABASE_URL ?? 'https://ueostzaevpteuxdmxnww.supabase.co';
const SUPABASE_ANON_KEY =
  import.meta.env.VITE_SUPABASE_ANON_KEY ?? 'sb_publishable_w-qzzDRNu57d5YZ3EQ9NNw_d19zjgeW';

const SESSION_KEY = 'nectar.auth.session';

export interface AuthSession {
  access_token: string;
  refresh_token?: string;
  expires_at?: number;
  user?: {
    id?: string;
    email?: string;
    user_metadata?: Record<string, unknown>;
  };
}

function authHeaders() {
  return {
    apikey: SUPABASE_ANON_KEY,
    Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    'Content-Type': 'application/json',
  };
}

export function getStoredSession(): AuthSession | null {
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;

  try {
    const session = JSON.parse(raw) as AuthSession;
    if (session.expires_at && session.expires_at * 1000 < Date.now()) {
      clearStoredSession();
      return null;
    }
    return session.access_token ? session : null;
  } catch {
    clearStoredSession();
    return null;
  }
}

export function storeSession(session: AuthSession) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession() {
  window.localStorage.removeItem(SESSION_KEY);
}

export function consumeOAuthHash(): AuthSession | null {
  const hash = window.location.hash.startsWith('#')
    ? window.location.hash.slice(1)
    : window.location.hash;

  if (!hash.includes('access_token=')) return null;

  const params = new URLSearchParams(hash);
  const accessToken = params.get('access_token');
  if (!accessToken) return null;

  const expiresIn = Number(params.get('expires_in') ?? '3600');
  const session: AuthSession = {
    access_token: accessToken,
    refresh_token: params.get('refresh_token') ?? undefined,
    expires_at: Math.floor(Date.now() / 1000) + expiresIn,
  };

  storeSession(session);
  window.history.replaceState(null, document.title, window.location.pathname + window.location.search);
  return session;
}

export async function signInWithPassword(email: string, password: string): Promise<AuthSession> {
  const response = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ email, password }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error_description || payload.msg || 'Unable to sign in');
  }

  const session: AuthSession = {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    expires_at: payload.expires_at,
    user: payload.user,
  };
  storeSession(session);
  return session;
}

export async function signUpWithPassword(email: string, password: string): Promise<AuthSession | null> {
  const response = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      email,
      password,
      data: {
        workspace: 'Nectar SDR Workspace',
      },
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error_description || payload.msg || 'Unable to create account');
  }

  if (!payload.access_token) {
    return null;
  }

  const session: AuthSession = {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    expires_at: payload.expires_at,
    user: payload.user,
  };
  storeSession(session);
  return session;
}

export function signInWithGoogle() {
  const redirectTo = `${window.location.origin}/login`;
  const params = new URLSearchParams({
    provider: 'google',
    redirect_to: redirectTo,
  });

  window.location.href = `${SUPABASE_URL}/auth/v1/authorize?${params.toString()}`;
}

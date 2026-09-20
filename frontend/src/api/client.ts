// The deployed Render backend URL (fallback when VITE_API_BASE_URL is not set in Vercel env vars)
const RENDER_BACKEND_URL = 'https://autonomous-sdr-backend.onrender.com';

const configuredApiUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/$/, '');

const BASE_URL = configuredApiUrl
  || (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : RENDER_BACKEND_URL);

// Demo mode — set VITE_DEMO_MODE=true in Vercel env vars to disable real API calls
export const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true';

export async function fakeDelay(ms = 800): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

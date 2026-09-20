const DEFAULT_LOCAL_API = 'http://localhost:8000';
const configuredApiUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/$/, '');
const BASE_URL = configuredApiUrl ||
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? DEFAULT_LOCAL_API
    : '');

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  if (!BASE_URL) {
    throw new Error(
      'API base URL is not configured. Set VITE_API_BASE_URL to your Render backend URL, for example: https://your-app.onrender.com'
    );
  }

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

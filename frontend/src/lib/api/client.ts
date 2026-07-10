/** Base fetch wrapper — attaches the bearer token when present.
 *  Handles Pydantic 422 detail shapes (list of {loc, msg}) so toasts
 *  never say "[object Object]" — CyberFraud lesson from day one. */

const AUTH_TOKEN_KEY = 'zerofir_token';

export function getToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token === null) localStorage.removeItem(AUTH_TOKEN_KEY);
  else localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    setToken(null);
    if (window.location.pathname !== '/login') window.location.href = '/login';
    throw new Error('Session expired — please log in again.');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    // Backend already turns Pydantic 422 into a plain-English string via
    // utils/friendly_errors.py, so `detail` is typically a string. Keep
    // the array-branch anyway for defensive parity with CyberFraud.
    let message: string;
    const detail = body?.detail;
    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail
        .map((e: { loc?: (string | number)[]; msg?: string }) => {
          const loc = Array.isArray(e.loc)
            ? e.loc.filter((x) => x !== 'body').join('.')
            : '';
          const msg = e.msg ?? 'invalid value';
          return loc ? `${loc}: ${msg}` : msg;
        })
        .join('; ');
    } else if (detail && typeof detail === 'object') {
      message = JSON.stringify(detail);
    } else {
      message = `HTTP ${res.status}`;
    }
    throw new Error(message);
  }

  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return null as T;
  }
  return res.json() as Promise<T>;
}

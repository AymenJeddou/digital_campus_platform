// Same-origin client for the backend. Every call goes through the Next.js
// proxy at /api/*, which attaches the session token from an httpOnly cookie:
// the token itself is never readable by page JavaScript.

import type { Messages } from './dictionary';

export class ApiError extends Error {
  constructor(public status: number, public detail: string) {
    super(detail);
  }
}

type Options = { method?: string; json?: unknown; form?: FormData; signal?: AbortSignal };

export async function request(path: string, { method, json, form, signal }: Options = {}): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`/api/${path.replace(/^\//, '')}`, {
      method: method ?? (json || form ? 'POST' : 'GET'),
      headers: json !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: json !== undefined ? JSON.stringify(json) : form,
      signal,
      cache: 'no-store',
    });
  } catch (err) {
    if ((err as Error).name === 'AbortError') throw err;
    throw new ApiError(0, 'offline');
  }
  if (res.status === 401 && !path.startsWith('auth/') && !path.startsWith('sources')) {
    // Session expired or revoked: back to login, then back here.
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login?next=${next}`;
    throw new ApiError(401, 'Not authenticated');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : `HTTP ${res.status}`;
    throw new ApiError(res.status, detail);
  }
  return res;
}

export async function api<T = unknown>(path: string, options: Options = {}): Promise<T> {
  const res = await request(path, options);
  return res.status === 204 ? (undefined as T) : res.json();
}

/** Turn a backend error into copy the student can act on. */
export function errorMessage(err: unknown, t: Messages): string {
  if (!(err instanceof ApiError)) return t.common.error;
  if (err.status === 0) return t.common.offline;
  if (err.status === 429) return t.auth.errors.tooMany;
  const known: Record<string, string> = {
    'Invalid email or password': t.auth.errors.invalid,
    'Email not verified': t.auth.errors.unverified,
    'Email already registered': t.auth.errors.exists,
    'Invalid or expired reset link': t.auth.errors.badLink,
    'Invalid or expired verification link': t.auth.errors.badLink,
  };
  if (known[err.detail]) return known[err.detail];
  if (err.detail.startsWith('Password must')) return t.auth.errors.weak;
  // Upload/extraction errors are already specific and actionable.
  if ([413, 415, 422].includes(err.status) && err.detail !== 'Validation error') return err.detail;
  return t.common.error;
}

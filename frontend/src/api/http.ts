/** Client HTTP central: wrapper de fetch que injeta a base URL, o header
 * Authorization, e tenta refresh uma única vez em 401 antes de repetir.
 *
 * Refreshes concorrentes são deduplicados por uma promise compartilhada. */

import { tokenStore } from '../auth/tokenStore';

// Em produção o front é servido na mesma origem que a API (nginx faz proxy de
// /api → backend), então o default relativo '/api' basta. Em dev, defina
// VITE_API_BASE_URL no .env (ex.: http://localhost:8000/api).
const BASE = import.meta.env.VITE_API_BASE_URL ?? '/api';

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!tokenStore.refresh) return false;
  refreshing ??= (async () => {
    const resp = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: tokenStore.refresh }),
    });
    if (!resp.ok) {
      tokenStore.clear();
      return false;
    }
    tokenStore.set(await resp.json());
    return true;
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

export async function api<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (tokenStore.access) headers.set('Authorization', `Bearer ${tokenStore.access}`);

  const resp = await fetch(`${BASE}${path}`, { ...init, headers });

  if (resp.status === 401 && retry && (await tryRefresh())) {
    return api<T>(path, init, false);
  }
  if (resp.status === 401) {
    tokenStore.clear();
    window.location.assign('/login');
    throw new ApiError(401, null);
  }
  if (!resp.ok) throw new ApiError(resp.status, await resp.json().catch(() => null));
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

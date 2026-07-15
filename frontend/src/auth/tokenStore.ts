/** Armazenamento dos tokens de autenticação em localStorage.
 *
 * Trade-off de XSS aceito por simplicidade num app interno. */

const ACCESS = 'access_token';
const REFRESH = 'refresh_token';

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS);
  },
  get refresh() {
    return localStorage.getItem(REFRESH);
  },
  set(tokens: { access_token: string; refresh_token: string }) {
    localStorage.setItem(ACCESS, tokens.access_token);
    localStorage.setItem(REFRESH, tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS);
    localStorage.removeItem(REFRESH);
  },
};

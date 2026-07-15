/** Contexto de autenticação: login/logout contra o backend e estado autenticado. */

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { api } from '../api/http';
import { tokenStore } from './tokenStore';

interface TokenResponse {
  access_token: string;
  refresh_token: string;
}

interface AuthValue {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authed, setAuthed] = useState(() => !!tokenStore.access);

  const value = useMemo<AuthValue>(
    () => ({
      isAuthenticated: authed,
      async login(email, password) {
        const tokens = await api<TokenResponse>('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ username: email, password }),
        });
        tokenStore.set(tokens);
        setAuthed(true);
      },
      logout() {
        tokenStore.clear();
        setAuthed(false);
      },
    }),
    [authed],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth fora de <AuthProvider>');
  return ctx;
}

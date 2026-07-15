# Frontend — Fundação + Autenticação — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans para implementar este plano task-by-task. Os steps usam checkbox (`- [x]`).

> **Localização:** todo este plano roda no repositório do frontend: `../emissao_notas_fiscais_brand_open_frontend`.

**Ordem de execução:** Plano **3 de 5**. Pré-requisito dos Planos 4 e 5 (front de clientes e recorrências). Depende de o backend de auth já existir (`POST /auth/login`, `POST /auth/refresh` — já implementados).

**Goal:** Transformar o app de wizard-único numa SPA multi-página com **roteamento**, **camada de dados** (cache/loading/erro) e **autenticação** real contra o backend: tela de login, armazenamento de tokens, refresh automático em 401, rotas protegidas e um layout com navegação. Isto cria a base que os Planos 4 e 5 preenchem.

**Architecture:**
- **react-router-dom** para rotas; **@tanstack/react-query** para dados do servidor (queries/mutations com cache, loading e erro padronizados).
- **Client HTTP** central (`src/api/http.ts`): wrapper de `fetch` que injeta `VITE_API_BASE_URL`, header `Authorization: Bearer`, e em `401` tenta **refresh** uma vez e repete a requisição; se o refresh falhar, faz logout.
- **AuthContext** (`src/auth/AuthContext.tsx`): guarda `accessToken`/`refreshToken` (em `localStorage`), expõe `login`/`logout`/`isAuthenticated`. Tokens em `localStorage` por simplicidade (trade-off de XSS aceito para um app interno; documentar).
- **Rotas protegidas** via `<RequireAuth>` que redireciona para `/login` quando não autenticado.
- **Layout** com app-bar (reaproveitando o estilo atual) + nav lateral/topo para Clientes e Recorrências.

**Tech Stack:** React 19, Vite, TypeScript, react-router-dom v7, @tanstack/react-query v5.

---

## Estrutura de arquivos

**Criar:**
- `.env` / `.env.example` — `VITE_API_BASE_URL=http://localhost:8000`
- `src/api/http.ts` — wrapper de fetch + refresh.
- `src/auth/tokenStore.ts` — get/set/clear tokens em localStorage.
- `src/auth/AuthContext.tsx` — provider + `useAuth`.
- `src/auth/RequireAuth.tsx` — guard de rota.
- `src/pages/LoginPage.tsx`
- `src/components/AppLayout.tsx` — app-bar + nav + `<Outlet/>`.
- `src/router.tsx` — definição das rotas.
- `src/queryClient.ts` — instância do QueryClient.

**Modificar:**
- `package.json` — adicionar `react-router-dom`, `@tanstack/react-query`.
- `src/main.tsx` — montar `QueryClientProvider` + `AuthProvider` + `RouterProvider`.
- `src/App.tsx` — deixa de ser o wizard; o wizard de recorrências vai virar rota no Plano 5 (por ora, mover o wizard atual para `src/pages/recurrences/` intacto ou deixá-lo de lado).

---

### Task 1: Dependências e env

- [x] **Step 1:** instalar libs.

```bash
cd ../emissao_notas_fiscais_brand_open_frontend
npm install react-router-dom @tanstack/react-query
```

- [x] **Step 2:** criar `.env` e `.env.example`:

```
VITE_API_BASE_URL=http://localhost:8000
```

- [x] **Step 3:** garantir `.env` no `.gitignore` (manter `.env.example` versionado).

- [x] **Step 4: Commit**

```bash
git add package.json package-lock.json .env.example .gitignore
git commit -m "chore: adicionar react-router-dom e tanstack-query; env de API"
```

---

### Task 2: Token store e client HTTP

**Files:**
- Create: `src/auth/tokenStore.ts`, `src/api/http.ts`

- [x] **Step 1: `tokenStore.ts`**

```ts
const ACCESS = 'access_token';
const REFRESH = 'refresh_token';

export const tokenStore = {
  get access() { return localStorage.getItem(ACCESS); },
  get refresh() { return localStorage.getItem(REFRESH); },
  set(tokens: { access_token: string; refresh_token: string }) {
    localStorage.setItem(ACCESS, tokens.access_token);
    localStorage.setItem(REFRESH, tokens.refresh_token);
  },
  clear() { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH); },
};
```

- [x] **Step 2: `http.ts`** — wrapper com base URL, Authorization e refresh-on-401 (uma tentativa). Deduplicar refresh concorrente com uma promise compartilhada.

```ts
import { tokenStore } from '../auth/tokenStore';

const BASE = import.meta.env.VITE_API_BASE_URL ?? '';

export class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`HTTP ${status}`);
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
    if (!resp.ok) { tokenStore.clear(); return false; }
    tokenStore.set(await resp.json());
    return true;
  })().finally(() => { refreshing = null; });
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
```

- [x] **Step 3: Commit**

```bash
git add src/auth/tokenStore.ts src/api/http.ts
git commit -m "feat(auth): token store e client HTTP com refresh em 401"
```

---

### Task 3: AuthContext e guard

**Files:**
- Create: `src/auth/AuthContext.tsx`, `src/auth/RequireAuth.tsx`

- [x] **Step 1: `AuthContext.tsx`** — `login(email,password)` chama `POST /auth/login` (campo `username`=email), salva tokens; `logout()` limpa e navega.

```tsx
import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { api } from '../api/http';
import { tokenStore } from './tokenStore';

interface TokenResponse { access_token: string; refresh_token: string }

interface AuthValue {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authed, setAuthed] = useState(() => !!tokenStore.access);

  const value = useMemo<AuthValue>(() => ({
    isAuthenticated: authed,
    async login(email, password) {
      const tokens = await api<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username: email, password }),
      });
      tokenStore.set(tokens);
      setAuthed(true);
    },
    logout() { tokenStore.clear(); setAuthed(false); },
  }), [authed]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useAuth fora de <AuthProvider>');
  return ctx;
}
```

- [x] **Step 2: `RequireAuth.tsx`**

```tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

export function RequireAuth() {
  const { isAuthenticated } = useAuth();
  const loc = useLocation();
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: loc }} replace />;
  return <Outlet />;
}
```

- [x] **Step 3: Commit**

```bash
git add src/auth/AuthContext.tsx src/auth/RequireAuth.tsx
git commit -m "feat(auth): AuthContext (login/logout) e RequireAuth"
```

---

### Task 4: Login page e layout

**Files:**
- Create: `src/pages/LoginPage.tsx`, `src/components/AppLayout.tsx`

- [x] **Step 1: `LoginPage.tsx`** — form email/senha, usa `useAuth().login`, mostra erro de credencial, redireciona para `state.from` ou `/clientes` ao sucesso. Reaproveitar `primitives.tsx` (Field/Input) e classes de `base.css`.

- [x] **Step 2: `AppLayout.tsx`** — app-bar (manter "BRAND OPEN — Emissão de NFS-e"), nav com links `NavLink` para `/clientes` e `/recorrencias`, botão "Sair" (`logout`), e `<Outlet/>` no `main`.

- [x] **Step 3: Commit**

```bash
git add src/pages/LoginPage.tsx src/components/AppLayout.tsx
git commit -m "feat(ui): tela de login e layout autenticado com navegação"
```

---

### Task 5: Router, QueryClient e bootstrap

**Files:**
- Create: `src/router.tsx`, `src/queryClient.ts`
- Modify: `src/main.tsx`, `src/App.tsx`

- [x] **Step 1: `queryClient.ts`**

```ts
import { QueryClient } from '@tanstack/react-query';
export const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});
```

- [x] **Step 2: `router.tsx`** — rota pública `/login`; rotas protegidas sob `<RequireAuth>`+`<AppLayout>`: `/clientes`, `/recorrencias` (placeholders agora; preenchidos nos Planos 4 e 5). Redirect `/` → `/clientes`.

```tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RequireAuth } from './auth/RequireAuth';
import { AppLayout } from './components/AppLayout';
import { LoginPage } from './pages/LoginPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [{
      element: <AppLayout />,
      children: [
        { index: true, element: <Navigate to="/clientes" replace /> },
        { path: 'clientes', element: <div>Clientes (Plano 4)</div> },
        { path: 'recorrencias', element: <div>Recorrências (Plano 5)</div> },
      ],
    }],
  },
]);
```

- [x] **Step 3: `main.tsx`** — montar providers:

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router-dom';
import './styles/base.css';
import { queryClient } from './queryClient';
import { AuthProvider } from './auth/AuthContext';
import { router } from './router';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
```

> O wizard atual (`App.tsx`/`DpsProvider`/steps) **não é apagado** — será reaproveitado no Plano 5 como a rota de criação de recorrência. Mover esses arquivos para `src/pages/recurrences/` no Plano 5.

- [x] **Step 4:** rodar e validar o fluxo manualmente: `/login` autentica, redireciona, "Sair" volta ao login; rota protegida sem token redireciona.

```bash
npm run dev
npm run lint && npm run build
```

- [x] **Step 5: Commit**

```bash
git add src/router.tsx src/queryClient.ts src/main.tsx src/App.tsx
git commit -m "feat(app): roteamento, QueryClient e bootstrap autenticado"
```

---

## Checklist de conclusão

- [x] Login real contra `POST /auth/login`; tokens persistidos; refresh automático em 401; logout limpa e redireciona.
- [x] Rotas protegidas redirecionam para `/login` sem sessão.
- [x] Layout com navegação para Clientes e Recorrências.
- [x] `npm run lint` e `npm run build` verdes.

# Frontend — Gerenciamento de Clientes — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps com checkbox (`- [x]`).

> **Localização:** repositório do frontend `../emissao_notas_fiscais_brand_open_frontend`.

**Ordem de execução:** Plano **4 de 5**. Depende do Plano 3 (fundação + auth). Depende do Plano 1 (lookup de município, usado nos campos de endereço). O Plano 5 reutiliza o seletor/criação de cliente feito aqui.

**Goal:** CRUD completo de clientes contra os endpoints já existentes (`GET/POST/GET{id}/PATCH/DELETE /clients`): listagem paginada com busca, criação, edição e exclusão, reaproveitando os componentes de formulário/endereço já existentes no front.

**Architecture:**
- Camada de dados em `src/features/clients/`: tipos (espelhando `ClientRead/Create/Update`), funções de API (`api(...)`), e hooks TanStack Query (`useClients`, `useClient`, `useCreateClient`, `useUpdateClient`, `useDeleteClient`).
- Páginas: lista (`/clientes`), criação (`/clientes/novo`), edição (`/clientes/:id`).
- Formulário reaproveita `AddressFields` (com lookup de município real via Plano 1), `primitives.tsx` (Field/Input/Select) e o padrão de validação do front.
- Paginação e busca via query params do backend (`page`, `page_size`, `search`).

**Tech Stack:** React 19, react-router-dom, @tanstack/react-query, TypeScript.

---

## Contrato (espelha o backend)

```ts
// src/features/clients/types.ts
export interface Client {
  id: string;
  document: string;
  document_type: 'CPF' | 'CNPJ';
  name: string;
  municipal_registration: string | null;
  phone: string | null;
  email: string | null;
  zip_code: string | null;
  street: string | null;
  number: string | null;
  complement: string | null;
  neighborhood: string | null;
  ibge_city_code: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientCreate {
  document: string;
  name: string;
  municipal_registration?: string | null;
  phone?: string | null;
  email?: string | null;
  zip_code?: string | null;
  street?: string | null;
  number?: string | null;
  complement?: string | null;
  neighborhood?: string | null;
  ibge_city_code?: string | null;
}
export type ClientUpdate = Partial<ClientCreate>;

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

> **Regra do backend a respeitar no form:** os campos de endereço (`zip_code`, `street`, `number`, `neighborhood`, `ibge_city_code`) são **tudo-ou-nada** — se qualquer um for preenchido, todos viram obrigatórios. `complement` é livre. Validar isso no client antes de enviar (espelha o `model_validator` do backend).

---

## Estrutura de arquivos

**Criar:**
- `src/features/clients/types.ts`
- `src/features/clients/api.ts`
- `src/features/clients/hooks.ts`
- `src/features/clients/ClientForm.tsx`
- `src/pages/clients/ClientsListPage.tsx`
- `src/pages/clients/ClientCreatePage.tsx`
- `src/pages/clients/ClientEditPage.tsx`
- `src/components/lookups/MunicipioSelect.tsx` (autocomplete usando `/lookups/municipios`)

**Modificar:**
- `src/router.tsx` — rotas `/clientes`, `/clientes/novo`, `/clientes/:id`.
- `src/components/AddressFields.tsx` — trocar o mock `searchMunicipios` pelo lookup real (ou usar `MunicipioSelect`).

---

### Task 1: API e hooks

**Files:** Create `src/features/clients/{api,hooks}.ts`

- [x] **Step 1: `api.ts`**

```ts
import { api } from '../../api/http';
import type { Client, ClientCreate, ClientUpdate, Paginated } from './types';

export function listClients(p: { page?: number; page_size?: number; search?: string }) {
  const qs = new URLSearchParams();
  if (p.page) qs.set('page', String(p.page));
  if (p.page_size) qs.set('page_size', String(p.page_size));
  if (p.search) qs.set('search', p.search);
  return api<Paginated<Client>>(`/clients?${qs}`);
}
export const getClient = (id: string) => api<Client>(`/clients/${id}`);
export const createClient = (data: ClientCreate) =>
  api<Client>('/clients', { method: 'POST', body: JSON.stringify(data) });
export const updateClient = (id: string, data: ClientUpdate) =>
  api<Client>(`/clients/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteClient = (id: string) =>
  api<void>(`/clients/${id}`, { method: 'DELETE' });
```

- [x] **Step 2: `hooks.ts`** — queries/mutations com invalidação da lista.

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as apiClients from './api';

const KEY = ['clients'] as const;

export const useClients = (p: { page: number; search: string }) =>
  useQuery({ queryKey: [...KEY, p], queryFn: () => apiClients.listClients({ page: p.page, search: p.search }) });

export const useClient = (id: string) =>
  useQuery({ queryKey: [...KEY, id], queryFn: () => apiClients.getClient(id), enabled: !!id });

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: apiClients.createClient,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
export function useUpdateClient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof apiClients.updateClient>[1]) => apiClients.updateClient(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: apiClients.deleteClient,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEY }),
  });
}
```

- [x] **Step 3: Commit**

```bash
git add src/features/clients/types.ts src/features/clients/api.ts src/features/clients/hooks.ts
git commit -m "feat(clients): tipos, API e hooks tanstack-query"
```

---

### Task 2: Lookup de município real

**Files:** Create `src/components/lookups/MunicipioSelect.tsx`; Modify `src/components/AddressFields.tsx`

- [x] **Step 1:** criar `MunicipioSelect` — input com busca debounced que chama `/lookups/municipios?q=` (via `api`) e mostra opções `{value,label}`; valor controlado é o código IBGE.

```ts
// busca
import { api } from '../../api/http';
import type { Option } from '../../api/lookups'; // manter o type Option
export const searchMunicipiosApi = (q: string) =>
  api<Option[]>(`/lookups/municipios?q=${encodeURIComponent(q)}`);
```

- [x] **Step 2:** em `AddressFields.tsx`, substituir o import de `searchMunicipios` (mock) pela busca real. Manter a mesma assinatura `(q) => Promise<Option[]>` para não alterar o componente. Fazer o mesmo para `searchPaises` se endereço exterior for usado aqui (clientes são nacionais — manter só município).

- [x] **Step 3:** (opcional) marcar `src/api/lookups.ts` mock como deprecated ou apagar as funções já substituídas, mantendo só o `type Option` e `TABELA_ALIQUOTAS_SN` (ainda usado no Plano 5).

- [x] **Step 4: Commit**

```bash
git add src/components/lookups src/components/AddressFields.tsx
git commit -m "feat(lookups): município via API real nos campos de endereço"
```

---

### Task 3: Formulário de cliente

**Files:** Create `src/features/clients/ClientForm.tsx`

- [x] **Step 1:** form controlado com os campos de `ClientCreate`. Reusar `primitives.tsx` (Field/Input/Select) e `AddressFields`. Props: `initial?: Client`, `onSubmit(data)`, `submitting`, `serverError`.

- [x] **Step 2: validação client-side** espelhando o backend:
  - `document`: limpar não-dígitos, exigir 11 (CPF) ou 14 (CNPJ).
  - `name`: obrigatório, 1–150.
  - endereço **tudo-ou-nada**: se qualquer um de (`zip_code`,`street`,`number`,`neighborhood`,`ibge_city_code`) preenchido, todos obrigatórios; `zip_code` = 8 dígitos; `ibge_city_code` = 7 dígitos.
  - `email`: formato válido se informado.
- [x] **Step 3:** exibir erros por campo e o `serverError` (mensagem `{code,message,details}` do backend) num banner.

- [x] **Step 4: Commit**

```bash
git add src/features/clients/ClientForm.tsx
git commit -m "feat(clients): formulário reutilizável com validação espelhando o backend"
```

---

### Task 4: Páginas (lista, criar, editar) e rotas

**Files:** Create `src/pages/clients/{ClientsListPage,ClientCreatePage,ClientEditPage}.tsx`; Modify `src/router.tsx`

- [x] **Step 1: `ClientsListPage`** — busca (input com debounce → `search`), tabela (`document_type` + `document`, `name`, `email`, `phone`, `is_active`), paginação (`page`/`total`/`page_size`), estados loading/erro/vazio (TanStack Query), botão "Novo cliente", ações Editar/Excluir por linha. Excluir abre confirmação e chama `useDeleteClient` (tratar erro 409/RESTRICT se cliente tiver recorrências — mostrar mensagem do backend).

- [x] **Step 2: `ClientCreatePage`** — `ClientForm` + `useCreateClient`; ao sucesso, navegar para `/clientes`.

- [x] **Step 3: `ClientEditPage`** — carrega `useClient(:id)`, `ClientForm` com `initial`, `useUpdateClient` enviando só os campos alterados (`PATCH` parcial).

- [x] **Step 4: rotas** em `src/router.tsx` (sob o layout protegido):

```tsx
{ path: 'clientes', element: <ClientsListPage /> },
{ path: 'clientes/novo', element: <ClientCreatePage /> },
{ path: 'clientes/:id', element: <ClientEditPage /> },
```

- [x] **Step 5:** validar manualmente o CRUD ponta-a-ponta com o backend rodando.

```bash
npm run dev   # criar, listar, buscar, editar, excluir
npm run lint && npm run build
```

- [x] **Step 6: Commit**

```bash
git add src/pages/clients src/router.tsx
git commit -m "feat(clients): páginas de lista, criação e edição + rotas"
```

---

## Checklist de conclusão

- [x] Listagem com busca e paginação ligada ao backend.
- [x] Criar/editar/excluir funcionando; PATCH envia só os campos alterados.
- [x] Lookup de município real nos campos de endereço.
- [x] Validação client-side espelha as regras do backend (documento, endereço tudo-ou-nada).
- [x] Erros do backend (incl. RESTRICT ao excluir cliente com recorrências) exibidos com clareza.
- [x] `npm run lint` e `npm run build` verdes.

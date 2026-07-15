# Frontend — Recorrências via wizard (4 etapas + Agendamento) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) ou superpowers:executing-plans. Steps com checkbox (`- [ ]`).

> **Localização:** repositório do frontend `../emissao_notas_fiscais_brand_open_frontend`.

**Ordem de execução:** Plano **5 de 5** (último). Depende dos Planos 3 (fundação+auth), 4 (clientes / seletor de cliente), 1 (lookups reais) e 2 (backend aceitando `inf_dps`).

**Goal:** Reaproveitar o wizard de DPS existente para **criar recorrências**, com o fluxo: **Pessoas → Serviço → Valores → Agendamento → Revisar**. Ao confirmar, o front monta o `inf_dps` (sem `prest`/`dCompet`/calculados) e envia `POST /recurrences` com `client_id` (link), os campos de agendamento e o `inf_dps` (snapshot). Inclui a listagem de recorrências.

**Architecture:**
- O wizard atual (`DpsProvider` + `PessoasStep`/`ServicoStep`/`ValoresStep`/`RevisarStep`) é **movido** para `src/pages/recurrences/wizard/` e adaptado — nada é jogado fora.
- **Pessoas → cliente (link + snapshot):** a etapa passa a ligar o tomador a um cliente. O usuário **seleciona um cliente existente** (busca, reusando os hooks do Plano 4) **ou cria um novo inline** (cria via `POST /clients`, recebe `client_id`). Os dados do tomador continuam preenchidos no `Dps` (viram o snapshot `inf_dps.toma`). Guardar o `client_id` selecionado no estado do wizard.
- **Nova etapa Agendamento** entre Valores e Revisar: `day_of_month`, `start_date`, `end_date?`, `is_active`. `description` e `amount` da recorrência são **derivados** do DPS (`serv.cServ.xDescServ` e `valores.vServPrest.vServ`), não redigitados.
- **Serviço:** lookups passam a chamar a API real (`/lookups/*`) via Plano 1.
- **Submit:** monta `inf_dps` com `buildInfDps` adaptado (remover `prest`, `dCompet`, `tpEmit` opcional) e faz a mutation `useCreateRecurrence`.
- **Listagem** `/recorrencias` com TanStack Query.

**Tech Stack:** React 19, react-router-dom, @tanstack/react-query, TypeScript.

---

## Contrato da recorrência (espelha o backend, pós-Plano 2)

```ts
// src/features/recurrences/types.ts
export interface RecurrenceCreate {
  client_id: string;
  description: string;      // = inf_dps.serv.cServ.xDescServ
  amount: string;          // = inf_dps.valores.vServPrest.vServ (decimal string)
  day_of_month: number;    // 1..31
  start_date: string;      // AAAA-MM-DD
  end_date?: string | null;
  is_active: boolean;
  inf_dps: Record<string, unknown>; // saída de buildInfDps (sem prest/dCompet/calculados)
}

export interface Recurrence extends Omit<RecurrenceCreate, 'inf_dps'> {
  id: string;
  inf_dps: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
```

---

## Estrutura de arquivos

**Criar:**
- `src/features/recurrences/{types,api,hooks}.ts`
- `src/pages/recurrences/wizard/AgendamentoStep.tsx` (nova etapa)
- `src/pages/recurrences/RecurrenceWizardPage.tsx` (orquestra os passos; ex-`App.tsx`/`Wizard`)
- `src/pages/recurrences/RecurrencesListPage.tsx`
- `src/components/clients/ClientPicker.tsx` (selecionar existente ou criar novo)
- `src/state/wizardExtras.ts` ou ampliar `DpsContext` para guardar `client_id` + agendamento

**Mover/adaptar:**
- `src/pages/{PessoasStep,ServicoStep,ValoresStep,RevisarStep}.tsx` → `src/pages/recurrences/wizard/`
- `src/state/DpsContext.tsx`, `src/validation/dpsSchema.ts`, `src/payload/buildInfDps.ts`, `src/calc/derived.ts` → manter, ajustar imports

**Modificar:**
- `src/router.tsx` — `/recorrencias`, `/recorrencias/nova`
- `src/payload/buildInfDps.ts` — remover `prest`, `dCompet`; `tpEmit` opcional
- `src/pages/recurrences/wizard/ServicoStep.tsx` e `RevisarStep.tsx` — lookups reais

---

### Task 1: Mover o wizard para a área de recorrências

- [x] **Step 1:** mover os 4 steps, `DpsContext`, `dpsSchema`, `buildInfDps`, `derived`, `Stepper`, `StepNav` para `src/pages/recurrences/` (criar subpasta `wizard/` para os steps). Ajustar imports relativos. (Divergência: `DpsContext`/`dpsSchema`/`buildInfDps`/`derived` mantidos em `src/state`,`src/validation`,`src/payload`,`src/calc` porque são dependências de componentes compartilhados em `src/components` — mover quebraria a direção de dependência. Steps + Stepper + StepNav movidos para `wizard/`.)
- [x] **Step 2:** criar `RecurrenceWizardPage.tsx` a partir do antigo `Wizard` de `App.tsx`, agora montado pela rota `/recorrencias/nova` dentro do layout autenticado (sem o app-bar próprio — o layout já provê).
- [x] **Step 3:** garantir build verde após a mudança de imports.

```bash
npm run lint && npm run build
```

- [x] **Step 4: Commit** (fb719c2)

```bash
git commit -am "refactor(recurrences): mover wizard de DPS para a área de recorrências"
```

---

### Task 2: API e hooks de recorrências

**Files:** Create `src/features/recurrences/{api,hooks}.ts`

- [x] **Step 1: `api.ts`** — `listRecurrences`, `getRecurrence`, `createRecurrence`, `updateRecurrence` (espelhar `GET/POST/GET{id}/PATCH /recurrences`; **não há DELETE** — desativar via `is_active`).

```ts
import { api } from '../../api/http';
import type { Recurrence, RecurrenceCreate, Paginated } from './types';

export const listRecurrences = (p: { page?: number; client_id?: string; is_active?: boolean }) => {
  const qs = new URLSearchParams();
  if (p.page) qs.set('page', String(p.page));
  if (p.client_id) qs.set('client_id', p.client_id);
  if (p.is_active != null) qs.set('is_active', String(p.is_active));
  return api<Paginated<Recurrence>>(`/recurrences?${qs}`);
};
export const createRecurrence = (data: RecurrenceCreate) =>
  api<Recurrence>('/recurrences', { method: 'POST', body: JSON.stringify(data) });
```

- [x] **Step 2: `hooks.ts`** — `useRecurrences`, `useCreateRecurrence` (invalida lista). Padrão idêntico ao Plano 4.

- [x] **Step 3: Commit** (d2dbeb1)

```bash
git add src/features/recurrences
git commit -m "feat(recurrences): tipos, API e hooks tanstack-query"
```

---

### Task 3: Lookups reais no wizard

**Files:** Modify `ServicoStep.tsx`, `RevisarStep.tsx`, e os loaders

- [x] **Step 1:** trocar `searchMunicipios/searchPaises/searchListaServico/searchNBS` (mock de `src/api/lookups.ts`) por chamadas à API:

```ts
export const searchMunicipios = (q: string) => api<Option[]>(`/lookups/municipios?q=${encodeURIComponent(q)}`);
export const searchPaises     = (q: string) => api<Option[]>(`/lookups/paises?q=${encodeURIComponent(q)}`);
export const searchListaServico = (q: string) => api<Option[]>(`/lookups/servicos?q=${encodeURIComponent(q)}`);
export const searchNBS        = (q: string) => api<Option[]>(`/lookups/nbs?q=${encodeURIComponent(q)}`);
```

Manter o `type Option` e a assinatura `(q) => Promise<Option[]>` para `useOptions`/componentes não mudarem. `TABELA_ALIQUOTAS_SN` permanece local por ora.

- [x] **Step 2:** confirmar que `useOptions` segue funcionando (ele já lida com loader async). Assinatura `(q)=>Promise<Option[]>` mantida; `searchMunicipiosApi` preservado como alias.

- [x] **Step 3: Commit** (647abad)

```bash
git commit -am "feat(recurrences): lookups de serviço/NBS/município/país via API"
```

---

### Task 4: Etapa Pessoas → vínculo com cliente (ClientPicker)

**Files:** Create `src/components/clients/ClientPicker.tsx`; Modify `PessoasStep.tsx`; ampliar estado do wizard

- [x] **Step 1:** ampliar o estado do wizard para guardar `clientId: string | null` (e os campos de agendamento — Task 5). Novo contexto `WizardExtrasContext` (clientId + agendamento), conforme recomendado.
- [x] **Step 2: `ClientPicker`** — duas formas (selecionar existente via `useClients`; criar inline via `ClientForm`+`useCreateClient`). Ao escolher/criar: `onPick(client)` → pai seta `clientId` e pré-preenche `dps.toma.brasil`.
- [x] **Step 3:** em `PessoasStep`, `ClientPicker` no topo; campos do tomador editáveis (snapshot); `clientId` obrigatório para avançar. (Card "Dados da Prestação"/`dCompet` removido da etapa — não se aplica à recorrência; `dCompet` também removido de `validatePessoas`.)
- [x] **Step 4: Commit** (f1dc82e)

```bash
git add src/components/clients/ClientPicker.tsx
git commit -am "feat(recurrences): etapa Pessoas vincula tomador a um cliente (link + snapshot)"
```

---

### Task 5: Nova etapa Agendamento

**Files:** Create `src/pages/recurrences/wizard/AgendamentoStep.tsx`; Modify `RecurrenceWizardPage.tsx`, `Stepper`

- [x] **Step 1:** estender o stepper para 5 passos: `Pessoas, Serviço, Valores, Agendamento, Revisar`. Ajustar `VALIDATORS` e os índices em `RecurrenceWizardPage`.
- [x] **Step 2: `AgendamentoStep`** — campos:
  - `day_of_month` (1–31) — number/select;
  - `start_date` (date, obrigatório);
  - `end_date` (date, opcional; ≥ start_date — espelha validação do backend);
  - `is_active` (checkbox, default true).
  Guardar no `WizardExtrasContext`. Validar antes de avançar.
- [x] **Step 3: Commit** (9d72684)

```bash
git add src/pages/recurrences/wizard/AgendamentoStep.tsx
git commit -am "feat(recurrences): etapa de Agendamento (dia, início, fim, ativo)"
```

---

### Task 6: buildInfDps para recorrência + submit na Revisão

**Files:** Modify `buildInfDps.ts`, `RevisarStep.tsx`

- [x] **Step 1:** adaptar `buildInfDps` para o molde da recorrência: **remover** `prest` e `dCompet` da saída (o backend injeta na emissão). `tpEmit` mantido (default "1"). Resto igual (já omite vazios via `clean`). Stub `src/api/dpsClient.ts` removido (código morto após a troca).
- [x] **Step 2:** em `RevisarStep`, substituir o stub `submitDps` pela mutation `useCreateRecurrence` (`amount = parseMoney(vServ).toFixed(2)`, `day_of_month = Number(...)`).

```ts
const infDPS = buildInfDps(dps);
await createRecurrence.mutateAsync({
  client_id: clientId!,
  description: dps.serv.xDescServ,
  amount: parseMoney(dps.valores.vServ).toFixed(2),
  day_of_month: extras.dayOfMonth,
  start_date: extras.startDate,
  end_date: extras.endDate || null,
  is_active: extras.isActive,
  inf_dps: infDPS,
});
```

- [x] **Step 3:** ao sucesso: `reset()` do wizard + `extras.reset()` e navegar para `/recorrencias` com `state.created` (a lista mostra banner de sucesso). Em erro do backend, exibe `backendMessage` ({code,message,details}).
- [x] **Step 4:** texto da Revisão atualizado (agora cria a recorrência); aviso de campos calculados mantido. Card de Agendamento adicionado à revisão.
- [x] **Step 5: Commit** (bdd55d3)

```bash
git commit -am "feat(recurrences): revisar cria a recorrência (POST /recurrences com inf_dps)"
```

---

### Task 7: Listagem de recorrências e rotas

**Files:** Create `RecurrencesListPage.tsx`; Modify `src/router.tsx`

- [x] **Step 1: `RecurrencesListPage`** — tabela (tomador via `inf_dps.toma.xNome`, `description`, `amount`, `day_of_month`, `start_date`, `is_active`), filtros (`client_id`, `is_active`), paginação, botão "Nova recorrência". Estados loading/erro/vazio + banner de sucesso via `location.state.created`.
- [x] **Step 2:** rotas em `src/router.tsx`:

```tsx
{ path: 'recorrencias', element: <RecurrencesListPage /> },
{ path: 'recorrencias/nova', element: <RecurrenceWizardPage /> },
```

- [ ] **Step 3:** validar ponta-a-ponta: criar recorrência completa e conferir no backend que o `inf_dps` chegou correto e sem campos vazios; listar. (PENDENTE: backend não estava no ar durante a execução — `lint`/`build` verdes; validação manual ponta-a-ponta a ser feita com o backend rodando.)

```bash
npm run dev
npm run lint && npm run build
```

- [x] **Step 4: Commit** (f38b6df)

```bash
git add src/pages/recurrences/RecurrencesListPage.tsx src/router.tsx
git commit -m "feat(recurrences): listagem e rota de criação de recorrência"
```

---

## Checklist de conclusão

- [x] Wizard de 5 etapas (Pessoas, Serviço, Valores, Agendamento, Revisar) cria recorrência.
- [x] Pessoas vincula a um cliente (existente ou criado inline) → `client_id`; tomador vira snapshot em `inf_dps.toma`.
- [x] Lookups reais (município, país, serviço, NBS) no wizard.
- [x] `description`/`amount` derivados do DPS; agendamento coletado na etapa nova; `end_date ≥ start_date`.
- [x] `inf_dps` enviado sem `prest`/`dCompet`/calculados e sem campos vazios; recorrência criada via `POST /recurrences`.
- [x] Listagem de recorrências funcionando; `npm run lint`/`build` verdes. (Validação manual ponta-a-ponta pendente — backend não estava no ar.)

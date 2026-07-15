---
name: recorrencias-ui
description: Spec do módulo de recorrências — Frontend React (TypeScript)
metadata:
  type: project
---

# Spec — Módulo Recorrências (UI)

## Contexto

Interface de cadastro e gestão de recorrências de emissão mensal de NFS-e. Consome a
API descrita em `2026-06-13-recorrencias-api-design.md`. Inclui também a tela de
Próximas Notas (read-only), que consome o endpoint `/recurrences/upcoming`.

Depende de: [[clientes-ui]] (padrões visuais), [[recorrencias-api]]

---

## Rotas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/recurrences` | `RecurrencesListPage` | Listagem de recorrências |
| `/recurrences/new` | `RecurrenceFormPage` | Nova recorrência |
| `/recurrences/:id/edit` | `RecurrenceFormPage` | Editar recorrência |
| `/upcoming` | `UpcomingPage` | Próximas emissões (read-only) |

---

## Tela 1 — Listagem (`/recurrences`)

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Recorrências                              [+ Nova recorrência]  │
├──────────────────────────┬──────────────────────────────────────┤
│  Status: [Todas ▾]       │  🔍 Buscar cliente...               │
├──────────┬───────────┬───┴──┬──────────┬────────────┬──────────┤
│ Cliente  │ Descrição │ Valor│ Dia/mês  │ Vigência   │ Status   │ Ações   │
├──────────┼───────────┼──────┼──────────┼────────────┼──────────┤
│ Brand… │ Assessoria… │ R$ 1.500 │ 5 │ 01/01 → ∞ │ ● Ativa  │ Editar Inativar │
│ …        │ …         │ …    │ …        │ …          │ ○ Inativa│ Editar Reativar │
├─────────────────────────────────────────────────────────────────┤
│ ← 1 2 →                                    20 itens por página  │
└─────────────────────────────────────────────────────────────────┘
```

### Comportamento

- **Filtro Status**: dropdown com opções "Todas", "Ativas", "Inativas". Persiste em
  query param `?status=` na URL.
- **Busca por cliente**: filtragem client-side sobre a listagem já carregada (volume
  baixo, usuária única). Compara o texto digitado contra `client_name` de cada item
  (case-insensitive). Não dispara nova requisição à API.
- **Descrição**: truncada em 60 chars com reticências; tooltip com texto completo ao hover.
- **Valor**: formatado como `R$ 1.500,00`.
- **Dia/mês**: exibido como ordinal, ex: _"Dia 5"_, _"Dia 31"_. Tooltip: _"Se o dia não
  existir no mês, emite no último dia."_
- **Vigência**: `DD/MM/AAAA → DD/MM/AAAA` ou `DD/MM/AAAA → sem término`.
- **Status badge**: ● verde "Ativa" / ○ cinza "Inativa".
- **Ações inline**:
  - **Inativar** (quando ativa): chama `PATCH` com `{ is_active: false }`, atualiza
    linha na lista sem recarregar a página inteira, exibe toast _"Recorrência
    inativada."_
  - **Reativar** (quando inativa): chama `PATCH` com `{ is_active: true }`, toast
    _"Recorrência reativada."_
  - **Editar**: navega para `/recurrences/:id/edit`.
- **Paginação**: query params `?page=` na URL.
- **Estado vazio**: _"Nenhuma recorrência cadastrada."_ ou _"Nenhuma recorrência
  encontrada para os filtros selecionados."_

---

## Tela 2 — Formulário (`/recurrences/new` e `/recurrences/:id/edit`)

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Recorrências / Nova recorrência                               │
├─────────────────────────────────────────────────────────────────┤
│  Cliente *                                                       │
│  [🔍 Buscar cliente...                              ▾]           │
│                                                                 │
│  Descrição do serviço *                                         │
│  [                                                  ]           │
│  [                                       ] 0 / 1000            │
│                                                                 │
│  Valor do serviço (R$) *      Dia do mês *                      │
│  [R$ ____________]            [__]  (1 a 31)                    │
│  ℹ Se o dia não existir no mês, emite no último dia.            │
│                                                                 │
│  Data de início *             Data de término                   │
│  [DD/MM/AAAA    📅]           [DD/MM/AAAA    📅]  (opcional)    │
│                                                                 │
│  Ativa  [●───]                                                  │
│                                                                 │
│                                [Cancelar]  [Salvar]             │
└─────────────────────────────────────────────────────────────────┘
```

### Comportamento dos campos

**Cliente (select com busca)**
- Input de texto que chama `GET /clients?search=` com debounce 300 ms.
- Exibe dropdown com resultados (nome + CPF/CNPJ formatado).
- Ao selecionar, armazena `client_id` e exibe o nome.
- Limpa a seleção ao apagar o texto.

**Descrição do serviço**
- Textarea com contador de caracteres (`0 / 1000`).
- Cresce verticalmente conforme o conteúdo (min 3 linhas).

**Valor do serviço**
- Input numérico; aceita vírgula como separador decimal.
- Formatado como moeda ao perder o foco (ex: `1500` → `R$ 1.500,00`).
- Armazena internamente como número (ponto como separador) para envio à API.

**Dia do mês**
- Input numérico, 1–31.
- Nota informativa abaixo: _"Se o dia não existir no mês (ex: dia 31 em fevereiro), a emissão ocorre no último dia do mês."_

**Data de início / Data de término**
- Date pickers com formato `DD/MM/AAAA`.
- Data de término opcional; ao limpar, envia `null`.
- Validação: data de término ≥ data de início.

**Toggle Ativa**
- Exibido em modo criação (default: ligado).
- Útil para criar recorrências já inativas (pré-cadastro).

### Validação

| Campo | Regra |
|-------|-------|
| Cliente | Obrigatório |
| Descrição | Obrigatória; não vazia |
| Valor | Obrigatório; > 0 |
| Dia do mês | Obrigatório; 1–31 |
| Data de início | Obrigatória |
| Data de término | Se informada, ≥ data de início |

Erros aparecem abaixo do campo respectivo.

### Modo edição

- Ao entrar em `/recurrences/:id/edit`, busca `GET /recurrences/:id` e preenche o
  formulário.
- O campo Cliente exibe o nome do cliente atual; ao clicar, abre a busca novamente.
- Submissão usa `PATCH /recurrences/:id` com apenas os campos alterados.

### Submissão

- Botão **Salvar** desabilitado enquanto a requisição estiver em andamento (spinner).
- Sucesso: redireciona para `/recurrences` com toast _"Recorrência salva com sucesso."_
- **Cancelar**: volta para `/recurrences` sem confirmar.

---

## Tela 3 — Próximas Notas (`/upcoming`)

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Próximas Notas Fiscais                                          │
├──────────────────────────┬──────────────────────────────────────┤
│  De: [01/07/2026  📅]    │  Até: [31/07/2026  📅]              │
├──────────┬───────────────┬───────────────┬──────────────────────┤
│ Data     │ Cliente       │ Valor         │ Descrição            │
├──────────┼───────────────┼───────────────┼──────────────────────┤
│ 05/07    │ Brand Open    │ R$ 1.500,00   │ Assessoria de…       │
│ 31/07    │ …             │ …             │ …                    │
└──────────┴───────────────┴───────────────┴──────────────────────┘
```

### Comportamento

- **Período padrão**: mês corrente (`1º dia` ao `último dia` do mês atual).
- Ao alterar qualquer data, dispara nova chamada a `GET /recurrences/upcoming?from=&to=`
  com debounce de 400 ms.
- **Máximo de 90 dias**: se o intervalo selecionado exceder 90 dias, exibe mensagem
  inline abaixo dos seletores: _"O período máximo de visualização é de 90 dias."_ e
  não dispara a requisição.
- **Data**: exibida como `DD/MM/AAAA` (dia da semana abreviado opcional: `5ª 05/07`).
- **Descrição**: truncada em 50 chars; tooltip com texto completo.
- **Sem paginação** — a listagem é completa para o período (o volume é naturalmente
  limitado pelo intervalo de 90 dias e pelo número de recorrências ativas).
- **Estado vazio**: _"Nenhuma emissão agendada para o período selecionado."_
- **Estado de carregamento**: skeleton de tabela.
- Tela read-only: sem ações, sem botões de edição.

---

## Componentes

| Componente | Uso |
|-----------|-----|
| `RecurrencesListPage` | Listagem com filtros |
| `RecurrenceFormPage` | Formulário create/edit |
| `UpcomingPage` | Próximas notas (read-only) |
| `ClientSelect` | Select com busca de clientes (reutilizável) |
| `useRecurrences` | Hook: listagem paginada com filtros |
| `useRecurrence` | Hook: busca por ID |
| `useSaveRecurrence` | Hook: create (`POST`) ou update (`PATCH`) |
| `useToggleRecurrence` | Hook: ativar/inativar inline |
| `useUpcoming` | Hook: próximas emissões (`GET /recurrences/upcoming`) |

---

## Integração com a API

Mesmos padrões de autenticação e tratamento de erros definidos em [[clientes-ui]].

Mapeamento adicional de erros:
| Status | Contexto | Tratamento |
|--------|---------|-----------|
| 404 | `client_id` ao salvar | _"Cliente não encontrado."_ no campo Cliente |
| 422 | Intervalo > 90 dias em `/upcoming` | Validado no frontend antes da requisição |

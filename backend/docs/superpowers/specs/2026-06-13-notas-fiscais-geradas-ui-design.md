---
name: notas-fiscais-geradas-ui
description: Spec da tela de Notas Fiscais Geradas — histórico, retry, PDF/XML e botão de cron manual
metadata:
  type: project
---

# Spec — Notas Fiscais Geradas (UI)

## Contexto

Tela principal de operação do dia a dia: exibe o histórico de emissões, permite
baixar PDF/XML, reprocessar notas com falha e acionar o cron manualmente. Consome
os endpoints descritos em [[notas-fiscais-api]] e [[agendador-api]].

---

## Rota

| Rota | Componente |
|------|-----------|
| `/invoices` | `InvoicesPage` |

---

## Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Notas Fiscais Geradas               [⚡ Processar notas do dia]  │
├──────────────────────┬────────────────────────────────────────────┤
│  Status: [Todos ▾]   │  Cliente: [Todos ▾]  De: [__/__] Até:[__/__]│
├────────┬─────────────┬──────────┬──────────┬──────────┬──────────┤
│ Data   │ Cliente     │ Valor    │ Nº NF    │ Status   │ Ações    │
├────────┼─────────────┼──────────┼──────────┼──────────┼──────────┤
│ 13/06  │ Brand Open  │ R$ 1.500 │ 123456   │ ✅ Sucesso│ PDF XML  │
│ 13/06  │ Empresa X   │ R$ 800   │ —        │ ❌ Erro   │ Tentar novamente │
│ 05/06  │ Empresa Y   │ R$ 2.000 │ 123450   │ ✅ Sucesso│ PDF XML  │
├──────────────────────────────────────────────────────────────────┤
│ ← 1 2 3 →                                  20 itens por página  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Botão "Processar notas do dia"

- Posicionado no canto superior direito do cabeçalho.
- Chama `POST /cron/run` com o Bearer JWT da sessão.
- **Durante o processamento**: botão desabilitado com spinner e texto _"Processando…"_.
  Como o processamento pode levar vários minutos, o timeout do cliente HTTP deve ser
  120 s.
- **Ao concluir**: exibe modal de resumo com o resultado:

```
┌──────────────────────────────────────────┐
│  Resultado do processamento — 13/06/2026  │
│                                          │
│  ✅ 4 notas emitidas com sucesso          │
│  ❌ 1 nota com falha                      │
│                                          │
│  Sucessos:                               │
│  • Brand Open — NF nº 123456  [PDF]      │
│  • Empresa X  — NF nº 123457  [PDF]      │
│                                          │
│  Erros:                                  │
│  • Empresa Y — Timeout ao aguardar…      │
│                                          │
│                             [Fechar]     │
└──────────────────────────────────────────┘
```

- Após fechar o modal: recarrega a listagem.
- **Erro HTTP 5xx**: exibe banner _"Erro ao acionar o processamento. Tente novamente."_

---

## Filtros

| Filtro | Componente | Fonte |
|--------|-----------|-------|
| Status | Dropdown: Todos / Sucesso / Erro / Pendente / Processando | `?status=` |
| Cliente | Dropdown populado com clientes únicos das notas carregadas | client-side |
| De / Até | Date pickers | `?from=` / `?to=` |

- Default: **De** = 30 dias atrás; **Até** = hoje.
- Filtros persistidos como query params na URL.
- Alterar qualquer filtro dispara nova requisição com debounce de 300 ms.

---

## Tabela

| Coluna | Exibição |
|--------|---------|
| Data | `scheduled_date` formatado como `DD/MM/AAAA` |
| Cliente | `client_name` |
| Valor | Formatado como `R$ 1.500,00` |
| Nº NF | `nf_number` ou `—` se ausente |
| Status | Badge colorido (ver abaixo) |
| Ações | Botões contextuais (ver abaixo) |

### Badges de status

| Status | Badge |
|--------|-------|
| `success` | ✅ verde "Sucesso" |
| `error` | ❌ vermelho "Erro" — tooltip com `error_message` |
| `pending` | 🕐 cinza "Pendente" |
| `processing` | 🔄 azul "Processando" |

### Ações por linha

| Status | Ações disponíveis |
|--------|------------------|
| `success` | **PDF** (abre `GET /invoices/{id}/pdf` em nova aba) · **XML** (download `GET /invoices/{id}/xml`) |
| `error` | **Tentar novamente** |
| `pending` | — |
| `processing` | — |

### "Tentar novamente"

- Botão inline na linha da nota.
- Abre modal de confirmação: _"Deseja reprocessar a nota de [Cliente] do dia
  [Data]? Um novo número DPS será gerado."_
- Ao confirmar: chama `POST /invoices/{id}/retry` (timeout 120 s).
- Durante o processamento: spinner na linha, demais ações desabilitadas.
- Sucesso: atualiza a linha na tabela (novo status, novo nf_number, novas ações).
- Erro: exibe toast _"Falha ao reprocessar: [error_message]."_ e atualiza linha.

---

## Estado de carregamento e vazio

- **Carregando**: skeleton de tabela (5 linhas placeholder).
- **Sem resultados**: _"Nenhuma nota fiscal encontrada para os filtros selecionados."_
- **Sem notas ainda**: _"Nenhuma nota fiscal emitida ainda. Use o botão 'Processar notas do dia' para iniciar."_

---

## Componentes

| Componente | Uso |
|-----------|-----|
| `InvoicesPage` | Página principal |
| `CronRunModal` | Modal de resultado do cron |
| `RetryConfirmDialog` | Confirmação de reprocessamento |
| `InvoiceStatusBadge` | Badge de status reutilizável |
| `useInvoices` | Hook: listagem paginada com filtros |
| `useRunCron` | Hook: `POST /cron/run` |
| `useRetryInvoice` | Hook: `POST /invoices/{id}/retry` |

---

## Integração com a API

Mesmos padrões de autenticação e erros definidos em [[clientes-ui]].

Timeout elevado para `POST /cron/run` e `POST /invoices/{id}/retry`: **120 s**
(o processamento inclui polling da Betha que pode levar ~1 minuto).

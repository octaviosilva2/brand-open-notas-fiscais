---
name: notas-fiscais-api
description: Spec do módulo de notas fiscais geradas — histórico, retry, PDF e XML
metadata:
  type: project
---

# Spec — Módulo Notas Fiscais (API)

## Contexto

Armazena o resultado de cada tentativa de emissão de NFS-e. Criado pelo Agendador
antes da emissão e atualizado com o resultado. Expõe endpoints para consulta do
histórico, download de PDF/XML e reprocessamento de falhas.

Depende de: [[clientes-api]], [[recorrencias-api]], [[emissao-betha-api]]
Consumido por: [[agendador-api]], [[notas-fiscais-geradas-ui]]

---

## Modelo de domínio

### Entidade `Invoice`

| Campo | Tipo Python | Coluna SQL | Obrig. | Notas |
|-------|-------------|------------|--------|-------|
| `id` | `UUID` | `uuid` PK | S | `uuid7()` |
| `recurrence_id` | `UUID` | `uuid` FK | S | FK → `recurrences.id`, `ON DELETE RESTRICT` |
| `client_id` | `UUID` | `uuid` FK | S | FK → `clients.id`, desnormalizado para queries |
| `scheduled_date` | `date` | `date` | S | Dia em que o cron rodou / tentou emitir |
| `amount` | `Decimal(15,2)` | `numeric(15,2)` | S | Snapshot do valor na data de emissão |
| `description` | `str` | `varchar(1000)` | S | Snapshot da descrição na data de emissão |
| `status` | `str` | `varchar(20)` | S | `pending` \| `processing` \| `success` \| `error` |
| `n_dps` | `int \| None` | `integer` | N | Número DPS atribuído (definido antes do envio) |
| `protocol` | `str \| None` | `varchar(50)` | N | Protocolo retornado pela Betha |
| `nf_number` | `str \| None` | `varchar(50)` | N | Número da NF (em caso de sucesso) |
| `pdf_url` | `str \| None` | `varchar(500)` | N | URL do PDF (em caso de sucesso) |
| `xml_sent` | `str \| None` | `text` | N | XML completo enviado à Betha |
| `xml_response` | `str \| None` | `text` | N | Resposta bruta da Betha |
| `error_message` | `str \| None` | `varchar(1000)` | N | Mensagem de erro (em caso de falha) |
| `emission_date` | `datetime \| None` | `timestamptz` | N | Data/hora do resultado final |
| `created_at` | `datetime` | `timestamptz` | S | Auto |
| `updated_at` | `datetime` | `timestamptz` | S | Auto |

### Ciclo de vida do status

```
[cron inicia]
    → pending        (Invoice criado ou redefinido para retry)
    → processing     (enviado à Betha, aguardando polling)
    → success        (processado com sucesso)
       ou
    → error          (erro da Betha, timeout ou exceção inesperada)
```

Invoices com `status='processing'` há mais de 10 minutos são tratados como `error`
pelo endpoint de retry — protege contra falhas de processo durante o polling.

### Snapshot de dados

`amount` e `description` são copiados da recorrência no momento da criação do
Invoice. Isso garante que o histórico reflita os valores reais da emissão, mesmo
que a recorrência seja editada posteriormente.

---

## Estrutura de arquivos

```
app/modules/invoices/
  domain/
    entities.py
  application/
    ports/
      repository.py
      unit_of_work.py
    dtos/
      commands.py        # CreateInvoiceCommand, UpdateInvoiceCommand, InvoiceFilters
    use_cases/
      invoices_reader.py
      invoice_retryer.py
  adapters/
    http/
      router.py
      schemas.py         # InvoiceRead, InvoiceListRead
      dependencies.py
    db/
      models.py
      repository.py
      unit_of_work.py
      factories.py
```

---

## Endpoints

### `GET /invoices`

Lista notas com paginação e filtros. Inclui `client_name` via join.

**Query params:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `status` | `str` | — | `pending`, `processing`, `success`, `error` |
| `client_id` | `UUID` | — | Filtra por cliente |
| `from` | `date` | 30 dias atrás | Data de emissão inicial |
| `to` | `date` | hoje | Data de emissão final |
| `page` | `int` | `1` | |
| `page_size` | `int` | `20` | Máx 100 |

Ordenação: `scheduled_date DESC`, `created_at DESC`.

**Response 200:**
```json
{
  "items": [InvoiceRead],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

### `GET /invoices/{id}`

**Response 200:** `InvoiceRead` (todos os campos, incluindo `xml_sent` e `xml_response`)

**Erros:** `404 NotFoundError`

---

### `GET /invoices/{id}/xml`

Download do XML enviado à Betha.

**Response 200:**
```
Content-Type: application/xml
Content-Disposition: attachment; filename="dps_{nDPS}.xml"
```
Body: conteúdo de `xml_sent`.

**Erros:**
- `404 NotFoundError` — Invoice não encontrado
- `404 NotFoundError` — `xml_sent` é `None` (nota ainda não chegou a ser enviada)

---

### `GET /invoices/{id}/pdf`

Redireciona para a URL do PDF armazenado em `pdf_url`.

**Response 302:** `Location: {pdf_url}`

**Erros:**
- `404 NotFoundError` — Invoice não encontrado
- `404 NotFoundError` — `pdf_url` é `None` (nota sem sucesso)

---

### `POST /invoices/{id}/retry`

Reprocessa uma nota com falha. Disponível apenas para `status='error'`.
Invoices com `status='processing'` há mais de 10 minutos também são aceitos.

**Body:** nenhum

**Response 200:** `InvoiceRead` atualizado (com novo status `pending` ou já
`success`/`error` se o reprocessamento completar de forma síncrona)

> O retry roda de forma **síncrona** no request — o cliente aguarda o resultado
> completo (incluindo polling). Timeout HTTP do cliente deve ser ≥ 90 s.

**Erros:**
- `404 NotFoundError` — Invoice não encontrado
- `409 ConflictError` — `status` não é `error` (nem `processing` vencido): _"Esta
  nota não está disponível para reprocessamento."_

### Lógica do retry

1. Valida `status` (aceita `error`; aceita `processing` se `updated_at < now() - 10min`)
2. Redefine `status = 'pending'`, limpa `protocol`, `nf_number`, `pdf_url`,
   `xml_sent`, `xml_response`, `error_message`
3. Busca `n_dps` novo via `EmissionCounter.next_n_dps`
4. Chama `DpsPoller.emit_and_poll` → `EmissionResult`
5. Atualiza Invoice com resultado
6. Retorna `InvoiceRead`

---

## `InvoiceRead` schema

```python
id: UUID
recurrence_id: UUID
client_id: UUID
client_name: str          # desnormalizado via join
scheduled_date: date
amount: Decimal
description: str
status: Literal["pending", "processing", "success", "error"]
n_dps: int | None
protocol: str | None
nf_number: str | None
pdf_url: str | None
error_message: str | None
emission_date: datetime | None
created_at: datetime
updated_at: datetime
# xml_sent e xml_response omitidos na listagem; presentes apenas em GET /invoices/{id}
```

---

## Autenticação

Todos os endpoints exigem `get_current_actor` (Bearer JWT).

---

## Testes

### Unitários (`tests/unit/modules/invoices/`)

- Snapshot: `amount` e `description` refletem valores da recorrência no momento da
  criação, não após edição posterior.
- Retry: `status='success'` → 409; `status='error'` → aceito; `status='processing'`
  há 5 min → 409; há 15 min → aceito.

### Integração (`tests/integration/modules/invoices/`)

- Listagem com filtros: `status`, `client_id`, `from`/`to`.
- `GET /invoices/{id}/xml`: retorna XML correto; 404 quando `xml_sent` é `None`.
- `GET /invoices/{id}/pdf`: redirect 302 para `pdf_url`; 404 quando `None`.
- Retry com mock do `DpsPoller`: Invoice atualizado corretamente após retry.
- Paginação e ordenação.

---

## Migrações

Tabela `invoices` com todos os campos acima.
FKs `recurrence_id → recurrences.id` e `client_id → clients.id`, ambas `ON DELETE RESTRICT`.
**Unique constraint** em `(recurrence_id, scheduled_date)` — o retry atualiza a linha
existente em vez de criar outra; há sempre no máximo um Invoice por recorrência por dia.
Índice em `(status, scheduled_date)` para queries do cron.
Índice em `client_id`.

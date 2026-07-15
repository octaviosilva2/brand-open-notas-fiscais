---
name: recorrencias-api
description: Spec do módulo de recorrências — API backend (FastAPI + SQLAlchemy)
metadata:
  type: project
---

# Spec — Módulo Recorrências (API)

## Contexto

Módulo central do sistema: armazena as configurações de emissão mensal recorrente de
NFS-e. Cada recorrência vincula um cliente a um valor, descrição e dia do mês alvo.
O módulo de Agendador consulta as recorrências ativas para disparar as emissões.

Depende de: [[clientes-api]]

---

## Modelo de domínio

### Entidade `Recurrence`

| Campo | Tipo Python | Coluna SQL | Obrig. | Restrições |
|-------|-------------|------------|--------|------------|
| `id` | `UUID` | `uuid` PK | S | `uuid7()` |
| `client_id` | `UUID` | `uuid` FK | S | FK → `clients.id`, `ON DELETE RESTRICT` |
| `description` | `str` | `varchar(1000)` | S | Descrição do serviço (`xDescServ`) |
| `amount` | `Decimal` | `numeric(15,2)` | S | Valor do serviço em R$; > 0 |
| `day_of_month` | `int` | `smallint` | S | 1–31 (dia alvo de emissão) |
| `start_date` | `date` | `date` | S | Data de início da recorrência |
| `end_date` | `date \| None` | `date` | N | Data de término; se atingida, recorrência passa a inativa |
| `is_active` | `bool` | `boolean` | S | Default `True` |
| `created_at` | `datetime` | `timestamptz` | S | `server_default=now()` |
| `updated_at` | `datetime` | `timestamptz` | S | `server_default=now()` |

### Constantes de sistema (não armazenadas por recorrência)

Campos fixos para Brand Open — definidos em `app/core/settings.py`:

| Constante | Valor | Tag XML |
|-----------|-------|---------|
| `EMITTER_CNPJ` | `11222333000181` | `prest/CNPJ` |
| `SERVICE_CODE` | `170101` | `serv/cServ/cTribNac` |
| `NBS_CODE` | `114011400` | `serv/cServ/cNBS` |
| `CITY_CODE` | `4204608` | `serv/locPrest/cLocPrestacao` e `cLocEmi` |
| `TAX_RATE` | `2.01` | `tribMun/pAliq` |
| `TRIB_ISSQN` | `1` | `tribMun/tribISSQN` (operação tributável) |
| `RET_ISSQN` | `1` | `tribMun/tpRetISSQN` (não retido) |
| `OP_SIMP_NAC` | `3` | `prest/regTrib/opSimpNac` (optante ME/EPP) |
| `REG_AP_TRIB_SN` | `2` | `prest/regTrib/regApTribSN` |
| `REG_ESP_TRIB` | `0` | `prest/regTrib/regEspTrib` (nenhum) |

---

## Estrutura de arquivos

```
app/modules/recurrences/
  domain/
    entities.py          # Recurrence (dataclass frozen)
    rules.py             # resolve_emission_date, is_due_on
  application/
    ports/
      repository.py      # RecurrenceRepository (Protocol)
      unit_of_work.py    # RecurrencesUnitOfWork (Protocol)
    dtos/
      commands.py        # CreateRecurrenceCommand, UpdateRecurrenceCommand, RecurrenceFilters
    use_cases/
      recurrences_creator.py
      recurrences_updater.py
      recurrences_reader.py
      upcoming_reader.py   # calcula próximas emissões sem I/O extra
  adapters/
    http/
      router.py
      schemas.py         # RecurrenceCreate, RecurrenceUpdate, RecurrenceRead, UpcomingItem
      dependencies.py
    db/
      models.py
      repository.py
      unit_of_work.py
      factories.py
```

---

## Regra do último dia do mês

Lógica isolada em `domain/rules.py` para ser testável sem dependências:

```python
from calendar import monthrange
from datetime import date

def resolve_emission_date(year: int, month: int, day_of_month: int) -> date:
    """Resolve a data de emissão respeitando os limites do mês."""
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day_of_month, last_day))

def is_due_on(recurrence: Recurrence, target_date: date) -> bool:
    """Retorna True se a recorrência deve ser emitida na data alvo."""
    if not recurrence.is_active:
        return False
    if target_date < recurrence.start_date:
        return False
    if recurrence.end_date and target_date > recurrence.end_date:
        return False
    emission_date = resolve_emission_date(
        target_date.year, target_date.month, recurrence.day_of_month
    )
    return emission_date == target_date
```

---

## Endpoints

### `GET /recurrences`

Lista recorrências com paginação e filtros. Inclui `client_name` via join para evitar N+1.

**Query params:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `client_id` | `UUID` | — | Filtra por cliente |
| `is_active` | `bool` | — | `true` = ativas, `false` = inativas, ausente = todas |
| `page` | `int` | `1` | |
| `page_size` | `int` | `20` | Máx 100 |

**Response 200:**
```json
{
  "items": [RecurrenceRead],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### `POST /recurrences`

Cria nova recorrência.

**Body:** `RecurrenceCreate`

**Response 201:** `RecurrenceRead`

**Erros:**
- `404 NotFoundError` — `client_id` não encontrado

---

### `GET /recurrences/{id}`

**Response 200:** `RecurrenceRead`

**Erros:**
- `404 NotFoundError`

---

### `PATCH /recurrences/{id}`

Atualização parcial. Usado inclusive para ativar/inativar (`is_active`).

**Body:** `RecurrenceUpdate` (todos os campos opcionais, sentinel `UNSET`)

**Response 200:** `RecurrenceRead`

**Erros:**
- `404 NotFoundError`
- `404 NotFoundError` — novo `client_id` não encontrado (se alterado)

Sem `DELETE` — recorrências são preservadas para histórico e rastreabilidade.

---

### `GET /recurrences/upcoming`

Calcula as próximas emissões no período solicitado a partir das recorrências ativas.
Não consulta a tabela de invoices — é puramente computado.

**Query params:**

| Param | Tipo | Obrig. | Descrição |
|-------|------|--------|-----------|
| `from` | `date` | S | Data inicial (inclusive) |
| `to` | `date` | S | Data final (inclusive); máx 90 dias de `from` |

**Response 200:** lista ordenada por `scheduled_date`
```json
[
  {
    "recurrence_id": "uuid",
    "client_id": "uuid",
    "client_name": "Tomador Exemplo",
    "amount": 1500.00,
    "description": "Assessoria de marketing...",
    "scheduled_date": "2026-07-31"
  }
]
```

**Erros:**
- `422` — intervalo superior a 90 dias

**Algoritmo:**
1. Busca todas as recorrências ativas com `start_date <= to` e (`end_date IS NULL` OR `end_date >= from`)
2. Para cada recorrência, itera pelos meses que intersectam `[from, to]`
3. Para cada mês, chama `resolve_emission_date` e verifica se a data cai em `[from, to]`
4. Ordena resultado por `scheduled_date`, depois por `client_name`

---

## Schemas Pydantic

### `RecurrenceCreate`

```python
client_id: UUID
description: str           # max 1000, não vazio
amount: Decimal            # > 0, max 2 casas decimais
day_of_month: int          # 1–31
start_date: date
end_date: date | None = None
is_active: bool = True
```

Validador: `end_date >= start_date` quando informado.

### `RecurrenceUpdate`

Mesmos campos com `UNSET` como default.
Validador: se `end_date` e `start_date` ambos definidos, `end_date >= start_date`.

### `RecurrenceRead`

Todos os campos da entidade + campo desnormalizado `client_name: str`.

---

## Inativação automática por `end_date`

O job de emissão (`POST /cron/run`) já usa `is_due_on` que verifica `end_date`.
Recorrências vencidas não são emitidas — não há processo separado de inativação automática.

O campo `is_active` pode ser atualizado manualmente via `PATCH` a qualquer momento.

---

## Autenticação

Todos os endpoints exigem `get_current_actor` (Bearer JWT).

---

## Testes

### Unitários (`tests/unit/modules/recurrences/`)

- `resolve_emission_date`: dia 31 em fevereiro → último dia; dia 31 em março → 31; dia 28 em fevereiro → 28
- `is_due_on`: recorrência inativa; antes de start_date; depois de end_date; dia correto; dia errado
- Validação: amount ≤ 0; day_of_month = 0 ou 32; end_date < start_date

### Integração (`tests/integration/modules/recurrences/`)

- CRUD completo
- Listagem com filtros `is_active` e `client_id`
- `/upcoming`: recorrência dia 31 em fevereiro retorna 28 (ano não-bissexto) ou 29 (bissexto)
- `/upcoming`: recorrência com `end_date` expirado não aparece
- `/upcoming`: intervalo > 90 dias → 422
- FK: criar recorrência com `client_id` inexistente → 404

---

## Migrações

Tabela `recurrences` com todos os campos acima.
FK `client_id → clients.id` com `ON DELETE RESTRICT` (não deixa excluir cliente com recorrências).
Índice em `client_id`.
Índice em `(is_active, day_of_month)` para a query do cron.

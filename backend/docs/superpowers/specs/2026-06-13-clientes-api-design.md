---
name: clientes-api
description: Spec do módulo de clientes (tomadores) — API backend (FastAPI + SQLAlchemy)
metadata:
  type: project
---

# Spec — Módulo Clientes (API)

## Contexto

Módulo de cadastro e gerenciamento de tomadores de serviço. Os dados armazenados aqui
alimentam diretamente o elemento `toma` do XML da DPS enviado à Betha. É a fundação sobre
a qual o módulo de Recorrências depende.

---

## Modelo de domínio

### Entidade `Client`

| Campo | Tipo Python | Coluna SQL | Obrig. | Restrições |
|-------|-------------|------------|--------|------------|
| `id` | `UUID` | `uuid` PK | S | `uuid7()` |
| `document` | `str` | `varchar(14)` | S | Somente dígitos; 11 (CPF) ou 14 (CNPJ); único |
| `name` | `str` | `varchar(150)` | S | Não vazio |
| `municipal_registration` | `str \| None` | `varchar(15)` | N | Inscrição municipal |
| `phone` | `str \| None` | `varchar(20)` | N | |
| `email` | `str \| None` | `varchar(80)` | N | Formato e-mail válido |
| `zip_code` | `str \| None` | `varchar(8)` | N* | 8 dígitos numéricos |
| `street` | `str \| None` | `varchar(255)` | N* | Logradouro |
| `number` | `str \| None` | `varchar(60)` | N* | Número |
| `complement` | `str \| None` | `varchar(156)` | N | Complemento |
| `neighborhood` | `str \| None` | `varchar(60)` | N* | Bairro |
| `ibge_city_code` | `str \| None` | `varchar(7)` | N* | Código IBGE 7 dígitos |
| `is_active` | `bool` | `boolean` | S | Default `True` |
| `created_at` | `datetime` | `timestamptz` | S | `server_default=now()` |
| `updated_at` | `datetime` | `timestamptz` | S | `server_default=now()`, atualizado via trigger ou hook |

**N\*** = Opcional individualmente, mas se qualquer campo do grupo de endereço for
informado, todos os campos marcados com N\* passam a ser obrigatórios.

`document_type` ("CPF" ou "CNPJ") é **derivado** do comprimento do documento — não
armazenado. `len(document) == 11` → CPF; `len == 14` → CNPJ.

---

## Estrutura de arquivos

Seguir a anatomia hexagonal já estabelecida no projeto:

```
app/modules/clients/
  domain/
    entities.py          # Client (dataclass frozen)
  application/
    ports/
      repository.py      # ClientRepository (Protocol)
      unit_of_work.py    # ClientsUnitOfWork (Protocol)
    dtos/
      commands.py        # CreateClientCommand, UpdateClientCommand, ClientFilters
    use_cases/
      clients_creator.py
      clients_updater.py
      clients_reader.py
      clients_deleter.py
  adapters/
    http/
      router.py          # FastAPI router
      schemas.py         # Pydantic schemas (ClientCreate, ClientUpdate, ClientRead)
      dependencies.py    # DI: get_unit_of_work
    db/
      models.py          # SQLAlchemy ClientModel
      repository.py      # ClientRepository impl
      unit_of_work.py    # ClientsUnitOfWork impl
      factories.py       # model → entity
```

---

## Endpoints

### `GET /clients`

Lista clientes com paginação e busca opcional.

**Query params:**
| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `search` | `str` | `""` | Filtra por nome (ilike) ou documento (ilike) |
| `page` | `int` | `1` | Página atual |
| `page_size` | `int` | `20` | Itens por página (máx 100) |

**Response 200:**
```json
{
  "items": [ClientRead],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

### `POST /clients`

Cria novo cliente.

**Body:** `ClientCreate`

**Response 201:** `ClientRead`

**Erros:**
- `409 ConflictError` — documento já cadastrado

---

### `GET /clients/{id}`

Retorna um cliente pelo ID.

**Response 200:** `ClientRead`

**Erros:**
- `404 NotFoundError` — ID não encontrado

---

### `PATCH /clients/{id}`

Atualização parcial. Aceita qualquer subconjunto dos campos editáveis.

**Body:** `ClientUpdate` (todos os campos opcionais, sentinel `UNSET`)

**Response 200:** `ClientRead`

**Erros:**
- `404 NotFoundError`
- `409 ConflictError` — novo documento já pertence a outro cliente

---

### `DELETE /clients/{id}`

Remove o cliente permanentemente.

**Response 204:** sem body

**Erros:**
- `404 NotFoundError`
- `409 ConflictError` — cliente possui recorrências vinculadas (ativas ou inativas); mensagem: `"Cliente possui recorrências vinculadas e não pode ser excluído."`

---

## Schemas Pydantic

### `ClientCreate`

```python
document: str          # 11 ou 14 dígitos numéricos
name: str              # max 150
municipal_registration: str | None = None
phone: str | None = None
email: EmailStr | None = None
zip_code: str | None = None        # 8 dígitos
street: str | None = None
number: str | None = None
complement: str | None = None
neighborhood: str | None = None
ibge_city_code: str | None = None  # 7 dígitos
```

Validador de modelo: se qualquer campo de endereço for não-nulo, exige que
`zip_code`, `street`, `number`, `neighborhood` e `ibge_city_code` também sejam
não-nulos.

### `ClientUpdate`

Mesmos campos de `ClientCreate`, todos com `UNSET` como default — usa
`BaseUpdateCommand.defined_values()` para PATCH parcial.

### `ClientRead`

Todos os campos da entidade + campo calculado `document_type: Literal["CPF", "CNPJ"]`.

---

## Validação de documento

```python
def validate_document(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14):
        raise ValueError("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    return digits
```

Armazena somente dígitos. A formatação (pontos, barras, traços) é responsabilidade
do frontend.

---

## Autenticação

Todos os endpoints exigem `get_current_actor` (Bearer JWT) — mesmo padrão do módulo
`users`.

---

## Testes

### Unitários (`tests/unit/modules/clients/`)
- Validação do documento (CPF/CNPJ, inválido, com máscara)
- Regra do grupo de endereço (qualquer campo → todos obrigatórios)
- Derivação de `document_type`

### Integração (`tests/integration/modules/clients/`)
- CRUD completo (criar, ler, atualizar, listar, deletar)
- Conflito de documento duplicado → 409
- Deleção bloqueada com recorrência vinculada → 409
- Busca por nome parcial e por documento parcial
- Paginação

---

## Migrações

Criar migration Alembic: tabela `clients` com todos os campos acima.
Índice único em `document`.
Índice em `name` para performance da busca (ilike).

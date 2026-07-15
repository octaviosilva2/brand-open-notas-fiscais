# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão geral

Backend de CRM (FastAPI assíncrono + SQLAlchemy 2.0 async + PostgreSQL) organizado em
arquitetura hexagonal (ports & adapters) por módulo de domínio. Gerenciado com `uv`,
requer Python >= 3.14.

## Comandos

```bash
# Dependências (inclui grupo dev)
uv sync

# Rodar a API local
uv run uvicorn app.main:app --reload

# Lint / format / type-check
uv run ruff check .
uv run ruff format .
uv run mypy .

# Testes
uv run pytest                          # tudo
uv run pytest tests/unit               # só unitários
uv run pytest tests/integration        # só integração (precisa de Postgres, ver abaixo)
uv run pytest tests/unit/modules/users/domain/test_entities.py            # um arquivo
uv run pytest tests/integration/modules/users/test_users.py::test_nome    # um teste

# Migrações (Alembic — config em alembic.ini, scripts em migrations/)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "mensagem"

# Seed do usuário admin inicial
uv run python -m scripts.seed.initial_user

# Stack completa (Postgres + API + alembic upgrade no entrypoint)
docker compose up --build
```

Os testes de **integração** exigem um Postgres real. A URL vem de `TEST_DATABASE_URL`
(default `postgresql+asyncpg://postgres:senha@localhost:5432/brand_open`). Cada teste
roda dentro de uma transação com savepoint que sofre rollback ao final — o schema precisa
já existir (rode as migrações no banco de teste antes).

## Arquitetura

### Camadas (`app/`)

- **`app/core/`** — infraestrutura compartilhada, agnóstica de domínio: base de
  repositório/UoW, sessão de DB, paginação, segurança (JWT/senha), settings, exceções,
  handlers, middleware. **Regra fundamental: `app/core` NUNCA importa de `app/modules`**
  (a dependência aponta sempre dos módulos para o core, nunca o contrário).
- **`app/modules/<dominio>/`** — cada módulo é um slice hexagonal independente com a
  estrutura abaixo. Atualmente existe apenas `users`; novos domínios devem replicar o
  mesmo formato.
- **`app/api/router.py`** — monta o router raiz incluindo o router HTTP de cada módulo
  (com prefixo e tags). Único ponto que conhece todos os módulos.
- **`app/core/startup.py` → `create_app()`** — fábrica da app: registra exception
  handlers, middleware, rotas e o lifespan (`db.init()` / `db.close()`).

### Anatomia de um módulo (`app/modules/users/`)

```
domain/entities.py        → entidades (dataclasses frozen) + comandos de domínio
application/
  ports/                  → Protocols (UnitOfWork, Repository) — contratos que os
                            adapters satisfazem estruturalmente, sem herança
  dtos/                   → commands (entrada dos use cases) e filters (paginação)
  use_cases/              → 1 classe por operação (UsersCreator, UsersUpdater, ...);
                            recebem `uow` via construtor e dependem só dos Protocols
adapters/
  http/                   → router FastAPI, schemas Pydantic, dependencies (DI)
  db/                     → models SQLAlchemy, repository, unit_of_work, factories
```

### Fluxo de uma request

HTTP router → constrói `*Command` (DTO) a partir do schema Pydantic → instancia o use
case com o `UnitOfWork` injetado → use case abre `async with uow`, opera via
`uow.<repo>`, e o `__aexit__` faz commit (ou rollback em exceção) → retorna entidade de
domínio → router serializa em schema `*Read`.

### Padrões-chave

- **Unit of Work**: `BaseUnitOfWork` (core) é um context manager async que cria a sessão
  no `__aenter__` e commita/rollbacka no `__aexit__`. O UoW do módulo expõe os
  repositórios como propriedades (ex.: `uow.users`). Injetado nos endpoints via
  `make_unit_of_work` (sobrescrito nos testes com `app.dependency_overrides`).
- **Repository genérico**: `BaseRepository[ModelT, EntityT, FiltersT]` (core) traz CRUD +
  paginação. Subclasses definem `model`, `filters_type`, implementam `_to_entity` e
  sobrescrevem `_apply_filters`. O repositório converte sempre **model → entidade de
  domínio** na fronteira; use cases nunca veem models SQLAlchemy.
- **Ports como Protocols estruturais**: contratos em `application/ports/` são `Protocol`s.
  Os adapters os satisfazem por estrutura (duck typing tipado), sem herdar deles — isso
  mantém o domínio sem dependência das implementações.
- **Comandos e sentinel `UNSET`**: comandos são dataclasses frozen. Updates usam o
  sentinel `UNSET` (`app/core/types.py`) para distinguir "campo ausente" de "valor None".
  `BaseUpdateCommand.defined_values()` retorna só os campos efetivamente definidos —
  use-o para PATCHes parciais. Schemas usam `model_dump(exclude_unset=True)`.
- **Exceções**: levante as de `app/core/exceptions.py` (`NotFoundError`, `ConflictError`,
  `UnauthorizedError`, etc.). O handler em `app/core/handlers.py` as converte na resposta
  JSON `{code, message, details}` com o `status_code` correto.
- **Autenticação**: `HTTPBearer` → `decode_access_token` extrai o `sub` (UUID) →
  `get_current_actor` (no módulo users) resolve o `UserActor` validando que o usuário
  existe e está ativo. O router de users aplica `get_current_actor` como dependência
  global.
- **IDs**: chaves primárias usam `uuid.uuid7()` (ordenável temporalmente).

## Convenções

- **Idioma**: docstrings, comentários e mensagens de erro em português.
- Ruff (line-length 88, aspas duplas) e mypy `strict` são obrigatórios. `__init__.py` pode
  ter imports não usados (re-export). Testes têm regras de tipagem relaxadas.
- `pytest-asyncio` em `asyncio_mode = "auto"` — testes/fixtures async não precisam de
  decorator `@pytest.mark.asyncio`.
- Settings via pydantic-settings lendo `.env` (`extra="forbid"`). Defina
  `JWT_SECRET`/`JWT_ALGORITHM`/expirações e os `POSTGRES_*` (ou `DATABASE_URL` direto).

# Clientes API — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar o módulo de cadastro de clientes (tomadores de serviço) com CRUD completo, validação de CPF/CNPJ e busca paginada.

**Architecture:** Slice hexagonal independente em `app/modules/clients/`, seguindo exatamente o padrão do módulo `users` existente: domain entities → application ports/dtos/use_cases → adapters/db + adapters/http. A deleção captura `IntegrityError` do FK para gerar `ConflictError` semântico.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, PostgreSQL, Pydantic v2, Alembic, pytest-asyncio, httpx.

---

## Estrutura de arquivos

**Criar:**
- `app/modules/clients/__init__.py`
- `app/modules/clients/domain/__init__.py`
- `app/modules/clients/domain/entities.py`
- `app/modules/clients/application/__init__.py`
- `app/modules/clients/application/ports/__init__.py`
- `app/modules/clients/application/ports/repository.py`
- `app/modules/clients/application/ports/unit_of_work.py`
- `app/modules/clients/application/dtos/__init__.py`
- `app/modules/clients/application/dtos/commands.py`
- `app/modules/clients/application/dtos/filters.py`
- `app/modules/clients/application/use_cases/__init__.py`
- `app/modules/clients/application/use_cases/clients_creator.py`
- `app/modules/clients/application/use_cases/clients_reader.py`
- `app/modules/clients/application/use_cases/clients_updater.py`
- `app/modules/clients/application/use_cases/clients_deleter.py`
- `app/modules/clients/application/use_cases/clients_paginator.py`
- `app/modules/clients/adapters/__init__.py`
- `app/modules/clients/adapters/db/__init__.py`
- `app/modules/clients/adapters/db/models.py`
- `app/modules/clients/adapters/db/repository.py`
- `app/modules/clients/adapters/db/unit_of_work.py`
- `app/modules/clients/adapters/db/factories.py`
- `app/modules/clients/adapters/http/__init__.py`
- `app/modules/clients/adapters/http/schemas.py`
- `app/modules/clients/adapters/http/dependencies.py`
- `app/modules/clients/adapters/http/router.py`
- `tests/unit/modules/clients/__init__.py`
- `tests/unit/modules/clients/test_entities.py`
- `tests/integration/modules/clients/__init__.py`
- `tests/integration/modules/clients/conftest.py`
- `tests/integration/modules/clients/test_clients.py`

**Modificar:**
- `app/api/router.py` — registrar router de clientes
- `migrations/env.py` — importar `ClientModel`

**Migration (gerada via Alembic autogenerate):**
- `migrations/versions/<hash>_add_clients_table.py`

---

### Task 1: Domain entities

**Files:**
- Create: `app/modules/clients/domain/entities.py`
- Create: `app/modules/clients/domain/__init__.py`
- Create: `app/modules/clients/__init__.py`

- [ ] **Step 1: Criar os arquivos `__init__.py` vazios**

```bash
touch app/modules/clients/__init__.py app/modules/clients/domain/__init__.py
```

- [ ] **Step 2: Escrever `domain/entities.py`**

```python
# app/modules/clients/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewClient(BaseCreateCommand):
    document: str
    name: str
    municipal_registration: str | None
    phone: str | None
    email: str | None
    zip_code: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    ibge_city_code: str | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class UpdateClient(BaseUpdateCommand):
    document: str | Unset = UNSET
    name: str | Unset = UNSET
    municipal_registration: str | None | Unset = UNSET
    phone: str | None | Unset = UNSET
    email: str | None | Unset = UNSET
    zip_code: str | None | Unset = UNSET
    street: str | None | Unset = UNSET
    number: str | None | Unset = UNSET
    complement: str | None | Unset = UNSET
    neighborhood: str | None | Unset = UNSET
    ibge_city_code: str | None | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Client:
    id: uuid.UUID
    document: str
    name: str
    municipal_registration: str | None
    phone: str | None
    email: str | None
    zip_code: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    ibge_city_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def document_type(self) -> Literal["CPF", "CNPJ"]:
        return "CPF" if len(self.document) == 11 else "CNPJ"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document": self.document,
            "name": self.name,
            "municipal_registration": self.municipal_registration,
            "phone": self.phone,
            "email": self.email,
            "zip_code": self.zip_code,
            "street": self.street,
            "number": self.number,
            "complement": self.complement,
            "neighborhood": self.neighborhood,
            "ibge_city_code": self.ibge_city_code,
            "is_active": self.is_active,
            "document_type": self.document_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/clients/
git commit -m "feat(clients): domain entities"
```

---

### Task 2: Unit tests — entidades e validações

**Files:**
- Create: `tests/unit/modules/clients/__init__.py`
- Create: `tests/unit/modules/clients/test_entities.py`

- [ ] **Step 1: Escrever testes unitários**

```python
# tests/unit/modules/clients/test_entities.py
import re
import uuid
from datetime import UTC, datetime

import pytest

from app.modules.clients.domain.entities import Client


def _make_client(document: str) -> Client:
    return Client(
        id=uuid.uuid4(),
        document=document,
        name="Empresa Teste",
        municipal_registration=None,
        phone=None,
        email=None,
        zip_code=None,
        street=None,
        number=None,
        complement=None,
        neighborhood=None,
        ibge_city_code=None,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_document_type_cpf():
    client = _make_client("12345678901")
    assert client.document_type == "CPF"


def test_document_type_cnpj():
    client = _make_client("12345678000195")
    assert client.document_type == "CNPJ"


def _validate_document(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14):
        raise ValueError("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    return digits


def test_validate_document_strips_mask():
    assert _validate_document("123.456.789-01") == "12345678901"


def test_validate_document_cnpj_strips_mask():
    assert _validate_document("12.345.678/0001-95") == "12345678000195"


def test_validate_document_invalid_length():
    with pytest.raises(ValueError, match="CPF deve ter 11"):
        _validate_document("1234567890")


def test_validate_document_13_digits_invalid():
    with pytest.raises(ValueError, match="CPF deve ter 11"):
        _validate_document("1234567890123")
```

- [ ] **Step 2: Rodar os testes**

```bash
uv run pytest tests/unit/modules/clients/ -v
```

Esperado: todos passam.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/modules/clients/
git commit -m "test(clients): unit tests para entidades"
```

---

### Task 3: Application ports

**Files:**
- Create: `app/modules/clients/application/ports/repository.py`
- Create: `app/modules/clients/application/ports/unit_of_work.py`
- Create: `app/modules/clients/application/__init__.py`
- Create: `app/modules/clients/application/ports/__init__.py`

- [ ] **Step 1: Escrever `ports/repository.py`**

```python
# app/modules/clients/application/ports/repository.py
import uuid
from typing import Protocol

from app.modules.clients.domain.entities import Client, NewClient, UpdateClient


class ClientsRepositoryProtocol(Protocol):
    async def get_by_id(self, id_: uuid.UUID) -> Client: ...
    async def get_by_id_or_none(self, id_: uuid.UUID) -> Client | None: ...
    async def get_by_document_or_none(self, document: str) -> Client | None: ...
    async def create(self, create_command: NewClient) -> Client: ...
    async def update(self, id_: uuid.UUID, update_command: UpdateClient) -> Client: ...
    async def delete(self, id_: uuid.UUID) -> None: ...
```

- [ ] **Step 2: Escrever `ports/unit_of_work.py`**

```python
# app/modules/clients/application/ports/unit_of_work.py
from types import TracebackType
from typing import Protocol, Self

from app.modules.clients.application.ports.repository import ClientsRepositoryProtocol


class ClientsUnitOfWorkProtocol(Protocol):
    @property
    def clients(self) -> ClientsRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
```

- [ ] **Step 3: Criar `__init__.py` vazios**

```bash
touch app/modules/clients/application/__init__.py
touch app/modules/clients/application/ports/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/clients/application/
git commit -m "feat(clients): application ports (protocols)"
```

---

### Task 4: Application DTOs

**Files:**
- Create: `app/modules/clients/application/dtos/commands.py`
- Create: `app/modules/clients/application/dtos/filters.py`
- Create: `app/modules/clients/application/dtos/__init__.py`

- [ ] **Step 1: Escrever `dtos/commands.py`**

```python
# app/modules/clients/application/dtos/commands.py
from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateClientCommand(BaseCreateCommand):
    document: str
    name: str
    municipal_registration: str | None = None
    phone: str | None = None
    email: str | None = None
    zip_code: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    ibge_city_code: str | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateClientCommand(BaseUpdateCommand):
    document: str | Unset = UNSET
    name: str | Unset = UNSET
    municipal_registration: str | None | Unset = UNSET
    phone: str | None | Unset = UNSET
    email: str | None | Unset = UNSET
    zip_code: str | None | Unset = UNSET
    street: str | None | Unset = UNSET
    number: str | None | Unset = UNSET
    complement: str | None | Unset = UNSET
    neighborhood: str | None | Unset = UNSET
    ibge_city_code: str | None | Unset = UNSET
    is_active: bool | Unset = UNSET
```

- [ ] **Step 2: Escrever `dtos/filters.py`**

```python
# app/modules/clients/application/dtos/filters.py
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClientFilters:
    search: str | None = None
```

- [ ] **Step 3: Criar `__init__.py`**

```bash
touch app/modules/clients/application/dtos/__init__.py
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/clients/application/dtos/
git commit -m "feat(clients): application DTOs"
```

---

### Task 5: Application use cases

**Files:**
- Create: `app/modules/clients/application/use_cases/clients_creator.py`
- Create: `app/modules/clients/application/use_cases/clients_reader.py`
- Create: `app/modules/clients/application/use_cases/clients_updater.py`
- Create: `app/modules/clients/application/use_cases/clients_deleter.py`
- Create: `app/modules/clients/application/use_cases/clients_paginator.py`
- Create: `app/modules/clients/application/use_cases/__init__.py`

- [ ] **Step 1: Escrever `clients_creator.py`**

```python
# app/modules/clients/application/use_cases/clients_creator.py
import uuid

from app.core.exceptions import ConflictError
from app.modules.clients.application.dtos.commands import CreateClientCommand
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client, NewClient


class ClientsCreator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def create(self, data: CreateClientCommand) -> Client:
        async with self._uow as uow:
            existing = await uow.clients.get_by_document_or_none(data.document)
            if existing:
                raise ConflictError(f"Cliente com documento '{data.document}' já existe.")
            return await uow.clients.create(
                NewClient(
                    document=data.document,
                    name=data.name,
                    municipal_registration=data.municipal_registration,
                    phone=data.phone,
                    email=data.email,
                    zip_code=data.zip_code,
                    street=data.street,
                    number=data.number,
                    complement=data.complement,
                    neighborhood=data.neighborhood,
                    ibge_city_code=data.ibge_city_code,
                    is_active=data.is_active,
                )
            )
```

- [ ] **Step 2: Escrever `clients_reader.py`**

```python
# app/modules/clients/application/use_cases/clients_reader.py
import uuid

from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client


class ClientsReader:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(self, id_: uuid.UUID) -> Client:
        async with self._uow as uow:
            return await uow.clients.get_by_id(id_)
```

- [ ] **Step 3: Escrever `clients_updater.py`**

```python
# app/modules/clients/application/use_cases/clients_updater.py
import uuid

from app.core.exceptions import ConflictError
from app.modules.clients.application.dtos.commands import UpdateClientCommand
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client, UpdateClient
from app.core.types import is_unset


class ClientsUpdater:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def update(self, id_: uuid.UUID, data: UpdateClientCommand) -> Client:
        async with self._uow as uow:
            if not is_unset(data.document):
                existing = await uow.clients.get_by_document_or_none(data.document)  # type: ignore[arg-type]
                if existing and existing.id != id_:
                    raise ConflictError(
                        f"Documento '{data.document}' já pertence a outro cliente."
                    )
            return await uow.clients.update(
                id_,
                UpdateClient(**data.defined_values()),
            )
```

- [ ] **Step 4: Escrever `clients_deleter.py`**

```python
# app/modules/clients/application/use_cases/clients_deleter.py
import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol


class ClientsDeleter:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def delete(self, id_: uuid.UUID) -> None:
        try:
            async with self._uow as uow:
                await uow.clients.delete(id_)
        except IntegrityError:
            raise ConflictError(
                "Cliente possui recorrências vinculadas e não pode ser excluído."
            )
```

- [ ] **Step 5: Escrever `clients_paginator.py`**

```python
# app/modules/clients/application/use_cases/clients_paginator.py
from app.core.pagination.params import Page, PageParams
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client


class ClientsPaginator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: ClientFilters | None = None,
    ) -> Page[Client]:
        async with self._uow as uow:
            return await uow.clients.paginate(
                page_params=page_params,
                filters=filters,
            )
```

- [ ] **Step 6: Criar `__init__.py`**

```bash
touch app/modules/clients/application/use_cases/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add app/modules/clients/application/use_cases/
git commit -m "feat(clients): application use cases"
```

---

### Task 6: DB adapter — model

**Files:**
- Create: `app/modules/clients/adapters/db/models.py`
- Create: `app/modules/clients/adapters/__init__.py`
- Create: `app/modules/clients/adapters/db/__init__.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/clients/adapters/__init__.py
touch app/modules/clients/adapters/db/__init__.py
```

- [ ] **Step 2: Escrever `adapters/db/models.py`**

```python
# app/modules/clients/adapters/db/models.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    document: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    municipal_registration: Mapped[str | None] = mapped_column(String(15), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(80), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    complement: Mapped[str | None] = mapped_column(String(156), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ibge_city_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_clients_document", "document", unique=True),
        Index("ix_clients_name", "name"),
    )
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/clients/adapters/
git commit -m "feat(clients): SQLAlchemy model"
```

---

### Task 7: DB adapter — repository e unit of work

**Files:**
- Create: `app/modules/clients/adapters/db/repository.py`
- Create: `app/modules/clients/adapters/db/unit_of_work.py`
- Create: `app/modules/clients/adapters/db/factories.py`

- [ ] **Step 1: Escrever `adapters/db/repository.py`**

```python
# app/modules/clients/adapters/db/repository.py
import uuid

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.domain.entities import Client


class ClientsRepository(BaseRepository[ClientModel, Client, ClientFilters]):
    model = ClientModel
    filters_type = ClientFilters

    def _to_entity(self, row: ClientModel) -> Client:
        return Client(
            id=row.id,
            document=row.document,
            name=row.name,
            municipal_registration=row.municipal_registration,
            phone=row.phone,
            email=row.email,
            zip_code=row.zip_code,
            street=row.street,
            number=row.number,
            complement=row.complement,
            neighborhood=row.neighborhood,
            ibge_city_code=row.ibge_city_code,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: ClientFilters) -> sa.Select:
        if filters.search:
            pattern = f"%{filters.search}%"
            stmt = stmt.where(
                sa.or_(
                    ClientModel.name.ilike(pattern),
                    ClientModel.document.ilike(pattern),
                )
            )
        return stmt

    async def get_by_document_or_none(self, document: str) -> Client | None:
        result = await self._session.execute(
            sa.select(self.model).where(self.model.document == document)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None
```

- [ ] **Step 2: Escrever `adapters/db/unit_of_work.py`**

```python
# app/modules/clients/adapters/db/unit_of_work.py
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.clients.adapters.db.repository import ClientsRepository


class ClientsUnitOfWork(BaseUnitOfWork):
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        super().__init__(session_factory=session_factory)
        self._clients: ClientsRepository | None = None

    @property
    def clients(self) -> ClientsRepository:
        if self._clients is None:
            raise RuntimeError("Repositório de clientes não inicializado.")
        return self._clients

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._clients = ClientsRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._clients = None
```

- [ ] **Step 3: Escrever `adapters/db/factories.py`**

```python
# app/modules/clients/adapters/db/factories.py
from app.core.db.session import db
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork


def make_unit_of_work() -> ClientsUnitOfWork:
    return ClientsUnitOfWork(session_factory=db.create_session)
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/clients/adapters/db/
git commit -m "feat(clients): DB repository e unit of work"
```

---

### Task 8: HTTP adapter — schemas

**Files:**
- Create: `app/modules/clients/adapters/http/schemas.py`
- Create: `app/modules/clients/adapters/http/__init__.py`

- [ ] **Step 1: Criar `__init__.py`**

```bash
touch app/modules/clients/adapters/http/__init__.py
```

- [ ] **Step 2: Escrever `adapters/http/schemas.py`**

```python
# app/modules/clients/adapters/http/schemas.py
import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

_ADDRESS_FIELDS = ("zip_code", "street", "number", "neighborhood", "ibge_city_code")


def _validate_document(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14):
        raise ValueError("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    return digits


class ClientCreate(BaseModel):
    document: str
    name: Annotated[str, Field(max_length=150, min_length=1)]
    municipal_registration: Annotated[str | None, Field(max_length=15)] = None
    phone: Annotated[str | None, Field(max_length=20)] = None
    email: EmailStr | None = None
    zip_code: Annotated[str | None, Field(max_length=8, pattern=r"^\d{8}$")] = None
    street: Annotated[str | None, Field(max_length=255)] = None
    number: Annotated[str | None, Field(max_length=60)] = None
    complement: Annotated[str | None, Field(max_length=156)] = None
    neighborhood: Annotated[str | None, Field(max_length=60)] = None
    ibge_city_code: Annotated[str | None, Field(max_length=7, pattern=r"^\d{7}$")] = None

    @field_validator("document", mode="before")
    @classmethod
    def validate_document(cls, v: str) -> str:
        return _validate_document(v)

    @model_validator(mode="after")
    def validate_address_group(self) -> "ClientCreate":
        has_any = any(getattr(self, f) is not None for f in _ADDRESS_FIELDS)
        if has_any:
            missing = [f for f in _ADDRESS_FIELDS if getattr(self, f) is None]
            if missing:
                raise ValueError(
                    f"Quando qualquer campo de endereço é informado, os campos "
                    f"{missing} também são obrigatórios."
                )
        return self


class ClientUpdate(BaseModel):
    document: str | None = None
    name: Annotated[str | None, Field(max_length=150, min_length=1)] = None
    municipal_registration: Annotated[str | None, Field(max_length=15)] = None
    phone: Annotated[str | None, Field(max_length=20)] = None
    email: EmailStr | None = None
    zip_code: Annotated[str | None, Field(max_length=8, pattern=r"^\d{8}$")] = None
    street: Annotated[str | None, Field(max_length=255)] = None
    number: Annotated[str | None, Field(max_length=60)] = None
    complement: Annotated[str | None, Field(max_length=156)] = None
    neighborhood: Annotated[str | None, Field(max_length=60)] = None
    ibge_city_code: Annotated[str | None, Field(max_length=7, pattern=r"^\d{7}$")] = None

    @field_validator("document", mode="before")
    @classmethod
    def validate_document(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_document(v)


class ClientRead(BaseModel):
    id: UUID
    document: str
    document_type: Literal["CPF", "CNPJ"]
    name: str
    municipal_registration: str | None
    phone: str | None
    email: str | None
    zip_code: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    ibge_city_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientsPaginationFilters(BaseModel):
    search: str | None = None
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/clients/adapters/http/schemas.py app/modules/clients/adapters/http/__init__.py
git commit -m "feat(clients): HTTP Pydantic schemas"
```

---

### Task 9: HTTP adapter — dependencies e router

**Files:**
- Create: `app/modules/clients/adapters/http/dependencies.py`
- Create: `app/modules/clients/adapters/http/router.py`

- [ ] **Step 1: Escrever `adapters/http/dependencies.py`**

```python
# app/modules/clients/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.clients.adapters.db.factories import make_unit_of_work
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork
from app.modules.clients.adapters.http.schemas import ClientsPaginationFilters
from app.modules.clients.application.dtos.filters import ClientFilters

ClientsUnitOfWorkDep = Annotated[ClientsUnitOfWork, Depends(make_unit_of_work)]


def get_pagination_filters(
    query_params: Annotated[ClientsPaginationFilters, Depends()],
) -> ClientFilters:
    return ClientFilters(search=query_params.search)


PaginationFiltersDep = Annotated[ClientFilters, Depends(get_pagination_filters)]
```

- [ ] **Step 2: Escrever `adapters/http/router.py`**

```python
# app/modules/clients/adapters/http/router.py
import uuid

from fastapi import APIRouter, Depends

from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.clients.adapters.http.dependencies import (
    ClientsUnitOfWorkDep,
    PaginationFiltersDep,
)
from app.modules.clients.adapters.http.schemas import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
)
from app.modules.clients.application.dtos.commands import (
    CreateClientCommand,
    UpdateClientCommand,
)
from app.modules.clients.application.use_cases.clients_creator import ClientsCreator
from app.modules.clients.application.use_cases.clients_deleter import ClientsDeleter
from app.modules.clients.application.use_cases.clients_paginator import ClientsPaginator
from app.modules.clients.application.use_cases.clients_reader import ClientsReader
from app.modules.clients.application.use_cases.clients_updater import ClientsUpdater
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("", response_model=PaginatedResponse[ClientRead])
async def list_clients(
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: ClientsUnitOfWorkDep,
) -> PaginatedResponse[ClientRead]:
    paginator = ClientsPaginator(uow=uow)
    page = await paginator.paginate(page_params=page_params, filters=filters)
    return build_paginated_response(
        items=[ClientRead.model_validate(c.to_dict()) for c in page.items],
        total=page.total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.post("", response_model=ClientRead, status_code=201)
async def create_client(
    data: ClientCreate,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    creator = ClientsCreator(uow=uow)
    client = await creator.create(
        CreateClientCommand(**data.model_dump(exclude_unset=True))
    )
    return ClientRead.model_validate(client.to_dict())


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    reader = ClientsReader(uow=uow)
    client = await reader.get_by_id(client_id)
    return ClientRead.model_validate(client.to_dict())


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    updater = ClientsUpdater(uow=uow)
    client = await updater.update(
        client_id,
        UpdateClientCommand(**data.model_dump(exclude_unset=True)),
    )
    return ClientRead.model_validate(client.to_dict())


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
) -> None:
    deleter = ClientsDeleter(uow=uow)
    await deleter.delete(client_id)
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/clients/adapters/http/
git commit -m "feat(clients): HTTP router e dependencies"
```

---

### Task 10: Registrar no router principal e migrations/env.py

**Files:**
- Modify: `app/api/router.py`
- Modify: `migrations/env.py`

- [ ] **Step 1: Atualizar `app/api/router.py`**

Adicionar após a linha `from app.modules.users.adapters.http.router import router as users_router`:

```python
from app.modules.clients.adapters.http.router import router as clients_router
```

E dentro de `build_api_router()`, após a linha do users_router:

```python
router.include_router(clients_router, prefix="/clients", tags=["Clientes"])
```

- [ ] **Step 2: Atualizar `migrations/env.py`**

Adicionar após a linha `import app.modules.users.adapters.db.models  # noqa: F401`:

```python
import app.modules.clients.adapters.db.models  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add app/api/router.py migrations/env.py
git commit -m "feat(clients): registrar router e model no alembic"
```

---

### Task 11: Migration Alembic

- [ ] **Step 1: Gerar a migration**

```bash
uv run alembic revision --autogenerate -m "add_clients_table"
```

Verificar que o arquivo gerado em `migrations/versions/` contém:
- Criação da tabela `clients` com todos os campos
- Índice único em `document`
- Índice em `name`

- [ ] **Step 2: Revisar o arquivo gerado**

Conferir que `upgrade()` cria a tabela e `downgrade()` a dropa corretamente.

- [ ] **Step 3: Aplicar no banco de teste**

```bash
uv run alembic upgrade head
```

Esperado: comando completa sem erros.

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/
git commit -m "feat(clients): migration tabela clients"
```

---

### Task 12: Integration tests

**Files:**
- Create: `tests/integration/modules/clients/__init__.py`
- Create: `tests/integration/modules/clients/conftest.py`
- Create: `tests/integration/modules/clients/test_clients.py`

- [ ] **Step 1: Escrever `conftest.py`**

```python
# tests/integration/modules/clients/conftest.py
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.modules.clients.adapters.db.models import Client as ClientModel


async def insert_client(
    db_connection: AsyncConnection,
    *,
    document: str = "12345678901",
    name: str = "Cliente Teste",
    is_active: bool = True,
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await db_connection.execute(
        insert(ClientModel).values(
            id=uid,
            document=document,
            name=name,
            municipal_registration=None,
            phone=None,
            email=None,
            zip_code=None,
            street=None,
            number=None,
            complement=None,
            neighborhood=None,
            ibge_city_code=None,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_client_id(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_client(db_connection)
```

- [ ] **Step 2: Atualizar `tests/integration/conftest.py`**

No fixture `client`, adicionar o override do UoW de clientes:

```python
from app.modules.clients.adapters.db.factories import make_unit_of_work as make_clients_uow
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork

def make_test_clients_uow() -> ClientsUnitOfWork:
    return ClientsUnitOfWork(session_factory=test_session_factory)

app.dependency_overrides[make_clients_uow] = make_test_clients_uow
```

- [ ] **Step 3: Escrever `test_clients.py`**

```python
# tests/integration/modules/clients/test_clients.py
import uuid

import pytest
from httpx import AsyncClient


@pytest.fixture
async def client_fixture(client: AsyncClient, db_connection, auth_headers):
    """Fixture que injeta client HTTP, db e headers de auth."""
    return client, auth_headers


async def test_create_client(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/clients",
        json={"document": "12345678901", "name": "Empresa ABC"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["document"] == "12345678901"
    assert data["document_type"] == "CPF"
    assert data["name"] == "Empresa ABC"


async def test_create_client_cnpj(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.post(
        "/clients",
        json={"document": "12345678000195", "name": "Empresa CNPJ"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["document_type"] == "CNPJ"


async def test_create_client_conflict(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.post(
        "/clients",
        json={"document": "12345678901", "name": "Outro"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_get_client(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get(f"/clients/{test_client_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(test_client_id)


async def test_get_client_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get(f"/clients/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_list_clients(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


async def test_search_clients_by_name(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients?search=Cliente", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["id"] == str(test_client_id) for i in items)


async def test_search_clients_by_document(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients?search=12345678901", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["id"] == str(test_client_id) for i in items)


async def test_search_clients_no_match(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients?search=XYZNAOENCONTRADO", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_update_client(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.patch(
        f"/clients/{test_client_id}",
        json={"name": "Nome Atualizado"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nome Atualizado"


async def test_update_client_document_conflict(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    from tests.integration.modules.clients.conftest import insert_client

    id1 = await insert_client(db_connection, document="11111111111", name="A")
    id2 = await insert_client(db_connection, document="22222222222", name="B")

    resp = await client.patch(
        f"/clients/{id2}",
        json={"document": "11111111111"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_delete_client(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    from tests.integration.modules.clients.conftest import insert_client

    uid = await insert_client(db_connection, document="99999999901", name="Para Deletar")
    resp = await client.delete(f"/clients/{uid}", headers=auth_headers)
    assert resp.status_code == 204


async def test_delete_client_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.delete(f"/clients/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/clients")
    assert resp.status_code == 403
```

- [ ] **Step 4: Rodar os testes de integração**

```bash
uv run pytest tests/integration/modules/clients/ -v
```

Esperado: todos passam.

- [ ] **Step 5: Commit final**

```bash
git add tests/integration/modules/clients/
git commit -m "test(clients): integration tests CRUD completo"
```

---

## Verificação final

- [ ] Rodar lint: `uv run ruff check app/modules/clients/ tests/unit/modules/clients/ tests/integration/modules/clients/`
- [ ] Rodar type check: `uv run mypy app/modules/clients/`
- [ ] Rodar todos os testes: `uv run pytest tests/unit/modules/clients/ tests/integration/modules/clients/ -v`
- [ ] Confirmar que testes pré-existentes ainda passam: `uv run pytest tests/ -v`

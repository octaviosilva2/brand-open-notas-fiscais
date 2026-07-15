# Recorrências API — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Pré-requisito:** O plano `2026-06-14-clientes-api.md` deve estar **completo e mergeado** antes de iniciar este plano. A migration `clients` deve existir no banco de teste.

**Goal:** Implementar o módulo de recorrências de NFS-e com CRUD completo, regra do último dia do mês, endpoint de próximas emissões (`/upcoming`) e filtros por cliente e status.

**Architecture:** Slice hexagonal em `app/modules/recurrences/`. A lógica de datas (`resolve_emission_date`, `is_due_on`) é isolada em `domain/rules.py` para ser testável sem I/O. O endpoint `/upcoming` é puramente computacional — não consulta a tabela `invoices`. FK `client_id → clients.id` com `ON DELETE RESTRICT` impede exclusão de clientes com recorrências.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, PostgreSQL, Pydantic v2, Alembic, pytest-asyncio, httpx.

---

## Estrutura de arquivos

**Criar:**
- `app/modules/recurrences/__init__.py`
- `app/modules/recurrences/domain/__init__.py`
- `app/modules/recurrences/domain/entities.py`
- `app/modules/recurrences/domain/rules.py`
- `app/modules/recurrences/application/__init__.py`
- `app/modules/recurrences/application/ports/__init__.py`
- `app/modules/recurrences/application/ports/repository.py`
- `app/modules/recurrences/application/ports/unit_of_work.py`
- `app/modules/recurrences/application/dtos/__init__.py`
- `app/modules/recurrences/application/dtos/commands.py`
- `app/modules/recurrences/application/dtos/filters.py`
- `app/modules/recurrences/application/use_cases/__init__.py`
- `app/modules/recurrences/application/use_cases/recurrences_creator.py`
- `app/modules/recurrences/application/use_cases/recurrences_reader.py`
- `app/modules/recurrences/application/use_cases/recurrences_updater.py`
- `app/modules/recurrences/application/use_cases/recurrences_paginator.py`
- `app/modules/recurrences/application/use_cases/upcoming_reader.py`
- `app/modules/recurrences/adapters/__init__.py`
- `app/modules/recurrences/adapters/db/__init__.py`
- `app/modules/recurrences/adapters/db/models.py`
- `app/modules/recurrences/adapters/db/repository.py`
- `app/modules/recurrences/adapters/db/unit_of_work.py`
- `app/modules/recurrences/adapters/db/factories.py`
- `app/modules/recurrences/adapters/http/__init__.py`
- `app/modules/recurrences/adapters/http/schemas.py`
- `app/modules/recurrences/adapters/http/dependencies.py`
- `app/modules/recurrences/adapters/http/router.py`
- `tests/unit/modules/recurrences/__init__.py`
- `tests/unit/modules/recurrences/test_rules.py`
- `tests/unit/modules/recurrences/test_entities.py`
- `tests/integration/modules/recurrences/__init__.py`
- `tests/integration/modules/recurrences/conftest.py`
- `tests/integration/modules/recurrences/test_recurrences.py`

**Modificar:**
- `app/api/router.py` — registrar router de recorrências
- `migrations/env.py` — importar `RecurrenceModel`

---

### Task 1: Domain entities e regras de domínio

**Files:**
- Create: `app/modules/recurrences/domain/entities.py`
- Create: `app/modules/recurrences/domain/rules.py`
- Create: `app/modules/recurrences/__init__.py`
- Create: `app/modules/recurrences/domain/__init__.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/recurrences/__init__.py app/modules/recurrences/domain/__init__.py
```

- [ ] **Step 2: Escrever `domain/entities.py`**

```python
# app/modules/recurrences/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewRecurrence(BaseCreateCommand):
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class UpdateRecurrence(BaseUpdateCommand):
    client_id: uuid.UUID | Unset = UNSET
    description: str | Unset = UNSET
    amount: Decimal | Unset = UNSET
    day_of_month: int | Unset = UNSET
    start_date: date | Unset = UNSET
    end_date: date | None | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Recurrence:
    id: uuid.UUID
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "description": self.description,
            "amount": self.amount,
            "day_of_month": self.day_of_month,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
```

- [ ] **Step 3: Escrever `domain/rules.py`**

```python
# app/modules/recurrences/domain/rules.py
from calendar import monthrange
from datetime import date

from app.modules.recurrences.domain.entities import Recurrence


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

- [ ] **Step 4: Commit**

```bash
git add app/modules/recurrences/
git commit -m "feat(recurrences): domain entities e regras de emissão"
```

---

### Task 2: Unit tests — regras de domínio

**Files:**
- Create: `tests/unit/modules/recurrences/__init__.py`
- Create: `tests/unit/modules/recurrences/test_rules.py`

- [ ] **Step 1: Escrever os testes unitários**

```python
# tests/unit/modules/recurrences/test_rules.py
import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.modules.recurrences.domain.entities import Recurrence
from app.modules.recurrences.domain.rules import is_due_on, resolve_emission_date


def _make_recurrence(
    day_of_month: int = 15,
    start_date: date = date(2026, 1, 1),
    end_date: date | None = None,
    is_active: bool = True,
) -> Recurrence:
    from datetime import UTC, datetime

    return Recurrence(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        description="Serviço",
        amount=Decimal("100.00"),
        day_of_month=day_of_month,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# resolve_emission_date
def test_resolve_emission_date_normal():
    assert resolve_emission_date(2026, 3, 15) == date(2026, 3, 15)


def test_resolve_emission_date_day_31_in_february_non_leap():
    assert resolve_emission_date(2026, 2, 31) == date(2026, 2, 28)


def test_resolve_emission_date_day_31_in_february_leap():
    assert resolve_emission_date(2028, 2, 31) == date(2028, 2, 29)


def test_resolve_emission_date_day_31_in_march():
    assert resolve_emission_date(2026, 3, 31) == date(2026, 3, 31)


def test_resolve_emission_date_day_31_in_april():
    assert resolve_emission_date(2026, 4, 31) == date(2026, 4, 30)


def test_resolve_emission_date_day_28_in_february():
    assert resolve_emission_date(2026, 2, 28) == date(2026, 2, 28)


# is_due_on
def test_is_due_on_inactive():
    rec = _make_recurrence(day_of_month=15, is_active=False)
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_before_start_date():
    rec = _make_recurrence(day_of_month=15, start_date=date(2026, 7, 1))
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_after_end_date():
    rec = _make_recurrence(day_of_month=15, end_date=date(2026, 5, 31))
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_correct_day():
    rec = _make_recurrence(day_of_month=15)
    assert is_due_on(rec, date(2026, 6, 15)) is True


def test_is_due_on_wrong_day():
    rec = _make_recurrence(day_of_month=15)
    assert is_due_on(rec, date(2026, 6, 16)) is False


def test_is_due_on_day_31_february():
    rec = _make_recurrence(day_of_month=31)
    assert is_due_on(rec, date(2026, 2, 28)) is True
    assert is_due_on(rec, date(2026, 2, 27)) is False


def test_is_due_on_no_end_date():
    rec = _make_recurrence(day_of_month=1, end_date=None)
    assert is_due_on(rec, date(2030, 12, 1)) is True
```

- [ ] **Step 2: Rodar os testes**

```bash
uv run pytest tests/unit/modules/recurrences/ -v
```

Esperado: todos passam.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/modules/recurrences/
git commit -m "test(recurrences): unit tests para regras de domínio"
```

---

### Task 3: Application ports e DTOs

**Files:**
- Create: `app/modules/recurrences/application/ports/repository.py`
- Create: `app/modules/recurrences/application/ports/unit_of_work.py`
- Create: `app/modules/recurrences/application/dtos/commands.py`
- Create: `app/modules/recurrences/application/dtos/filters.py`

- [ ] **Step 1: Escrever `ports/repository.py`**

```python
# app/modules/recurrences/application/ports/repository.py
import uuid
from datetime import date
from typing import Protocol

from app.modules.recurrences.domain.entities import (
    NewRecurrence,
    Recurrence,
    UpdateRecurrence,
)


class RecurrencesRepositoryProtocol(Protocol):
    async def get_by_id(self, id_: uuid.UUID) -> Recurrence: ...
    async def get_by_id_or_none(self, id_: uuid.UUID) -> Recurrence | None: ...
    async def create(self, create_command: NewRecurrence) -> Recurrence: ...
    async def update(self, id_: uuid.UUID, update_command: UpdateRecurrence) -> Recurrence: ...
    async def get_active_due_in_range(
        self, from_date: date, to_date: date
    ) -> list[Recurrence]: ...
```

- [ ] **Step 2: Escrever `ports/unit_of_work.py`**

```python
# app/modules/recurrences/application/ports/unit_of_work.py
from types import TracebackType
from typing import Protocol, Self

from app.modules.recurrences.application.ports.repository import (
    RecurrencesRepositoryProtocol,
)


class RecurrencesUnitOfWorkProtocol(Protocol):
    @property
    def recurrences(self) -> RecurrencesRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
```

- [ ] **Step 3: Escrever `dtos/commands.py`**

```python
# app/modules/recurrences/application/dtos/commands.py
import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateRecurrenceCommand(BaseCreateCommand):
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateRecurrenceCommand(BaseUpdateCommand):
    client_id: uuid.UUID | Unset = UNSET
    description: str | Unset = UNSET
    amount: Decimal | Unset = UNSET
    day_of_month: int | Unset = UNSET
    start_date: date | Unset = UNSET
    end_date: date | None | Unset = UNSET
    is_active: bool | Unset = UNSET
```

- [ ] **Step 4: Escrever `dtos/filters.py`**

```python
# app/modules/recurrences/application/dtos/filters.py
import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecurrenceFilters:
    client_id: uuid.UUID | None = None
    is_active: bool | None = None
```

- [ ] **Step 5: Criar `__init__.py`s**

```bash
touch app/modules/recurrences/application/__init__.py
touch app/modules/recurrences/application/ports/__init__.py
touch app/modules/recurrences/application/dtos/__init__.py
touch app/modules/recurrences/application/use_cases/__init__.py
```

- [ ] **Step 6: Commit**

```bash
git add app/modules/recurrences/application/
git commit -m "feat(recurrences): ports e DTOs"
```

---

### Task 4: Application use cases

**Files:**
- Create: `app/modules/recurrences/application/use_cases/recurrences_creator.py`
- Create: `app/modules/recurrences/application/use_cases/recurrences_reader.py`
- Create: `app/modules/recurrences/application/use_cases/recurrences_updater.py`
- Create: `app/modules/recurrences/application/use_cases/recurrences_paginator.py`
- Create: `app/modules/recurrences/application/use_cases/upcoming_reader.py`

- [ ] **Step 1: Escrever `recurrences_creator.py`**

```python
# app/modules/recurrences/application/use_cases/recurrences_creator.py
import uuid

from app.core.exceptions import NotFoundError
from app.modules.clients.adapters.db.factories import make_unit_of_work as make_clients_uow
from app.modules.recurrences.application.dtos.commands import CreateRecurrenceCommand
from app.modules.recurrences.application.ports.unit_of_work import RecurrencesUnitOfWorkProtocol
from app.modules.recurrences.domain.entities import NewRecurrence, Recurrence


class RecurrencesCreator:
    def __init__(
        self,
        uow: RecurrencesUnitOfWorkProtocol,
        clients_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def create(self, data: CreateRecurrenceCommand) -> Recurrence:
        # Valida que o client_id existe
        clients_uow = self._clients_uow_factory()
        async with clients_uow as cuow:
            client = await cuow.clients.get_by_id_or_none(data.client_id)
        if client is None:
            raise NotFoundError(f"Cliente com ID '{data.client_id}' não encontrado.")

        async with self._uow as uow:
            return await uow.recurrences.create(
                NewRecurrence(
                    client_id=data.client_id,
                    description=data.description,
                    amount=data.amount,
                    day_of_month=data.day_of_month,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    is_active=data.is_active,
                )
            )
```

- [ ] **Step 2: Escrever `recurrences_reader.py`**

```python
# app/modules/recurrences/application/use_cases/recurrences_reader.py
import uuid

from app.modules.recurrences.application.ports.unit_of_work import RecurrencesUnitOfWorkProtocol
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesReader:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(self, id_: uuid.UUID) -> Recurrence:
        async with self._uow as uow:
            return await uow.recurrences.get_by_id(id_)
```

- [ ] **Step 3: Escrever `recurrences_updater.py`**

```python
# app/modules/recurrences/application/use_cases/recurrences_updater.py
import uuid

from app.core.exceptions import NotFoundError
from app.core.types import is_unset
from app.modules.clients.adapters.db.factories import make_unit_of_work as make_clients_uow
from app.modules.recurrences.application.dtos.commands import UpdateRecurrenceCommand
from app.modules.recurrences.application.ports.unit_of_work import RecurrencesUnitOfWorkProtocol
from app.modules.recurrences.domain.entities import Recurrence, UpdateRecurrence


class RecurrencesUpdater:
    def __init__(
        self,
        uow: RecurrencesUnitOfWorkProtocol,
        clients_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def update(self, id_: uuid.UUID, data: UpdateRecurrenceCommand) -> Recurrence:
        if not is_unset(data.client_id):
            clients_uow = self._clients_uow_factory()
            async with clients_uow as cuow:
                client = await cuow.clients.get_by_id_or_none(data.client_id)  # type: ignore[arg-type]
            if client is None:
                raise NotFoundError(f"Cliente com ID '{data.client_id}' não encontrado.")

        async with self._uow as uow:
            return await uow.recurrences.update(
                id_,
                UpdateRecurrence(**data.defined_values()),
            )
```

- [ ] **Step 4: Escrever `recurrences_paginator.py`**

```python
# app/modules/recurrences/application/use_cases/recurrences_paginator.py
from app.core.pagination.params import Page, PageParams
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters
from app.modules.recurrences.application.ports.unit_of_work import RecurrencesUnitOfWorkProtocol
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesPaginator:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: RecurrenceFilters | None = None,
    ) -> Page[Recurrence]:
        async with self._uow as uow:
            return await uow.recurrences.paginate(
                page_params=page_params,
                filters=filters,
            )
```

- [ ] **Step 5: Escrever `upcoming_reader.py`**

```python
# app/modules/recurrences/application/use_cases/upcoming_reader.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

import sqlalchemy as sa

from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel
from app.modules.recurrences.application.ports.unit_of_work import RecurrencesUnitOfWorkProtocol
from app.modules.recurrences.domain.rules import resolve_emission_date
from app.modules.clients.adapters.db.models import Client as ClientModel


@dataclass(frozen=True)
class UpcomingItem:
    recurrence_id: UUID
    client_id: UUID
    client_name: str
    amount: Decimal
    description: str
    scheduled_date: date


class UpcomingReader:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def list_upcoming(
        self, from_date: date, to_date: date
    ) -> list[UpcomingItem]:
        async with self._uow as uow:
            recurrences_with_names = await uow.recurrences.get_active_due_in_range(
                from_date, to_date
            )

        results: list[UpcomingItem] = []
        # Iterate months between from_date and to_date
        year, month = from_date.year, from_date.month
        months: list[tuple[int, int]] = []
        while (year, month) <= (to_date.year, to_date.month):
            months.append((year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1

        for rec, client_name in recurrences_with_names:
            for y, m in months:
                emission_date = resolve_emission_date(y, m, rec.day_of_month)
                if from_date <= emission_date <= to_date:
                    results.append(
                        UpcomingItem(
                            recurrence_id=rec.id,
                            client_id=rec.client_id,
                            client_name=client_name,
                            amount=rec.amount,
                            description=rec.description,
                            scheduled_date=emission_date,
                        )
                    )

        results.sort(key=lambda x: (x.scheduled_date, x.client_name))
        return results
```

- [ ] **Step 6: Commit**

```bash
git add app/modules/recurrences/application/use_cases/
git commit -m "feat(recurrences): use cases"
```

---

### Task 5: DB adapter — model

**Files:**
- Create: `app/modules/recurrences/adapters/db/models.py`
- Create: `app/modules/recurrences/adapters/__init__.py`
- Create: `app/modules/recurrences/adapters/db/__init__.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/recurrences/adapters/__init__.py app/modules/recurrences/adapters/db/__init__.py
```

- [ ] **Step 2: Escrever `adapters/db/models.py`**

```python
# app/modules/recurrences/adapters/db/models.py
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class Recurrence(Base):
    __tablename__ = "recurrences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    day_of_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
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
        Index("ix_recurrences_client_id", "client_id"),
        Index("ix_recurrences_active_day", "is_active", "day_of_month"),
    )
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/recurrences/adapters/
git commit -m "feat(recurrences): SQLAlchemy model"
```

---

### Task 6: DB adapter — repository, UoW e factories

**Files:**
- Create: `app/modules/recurrences/adapters/db/repository.py`
- Create: `app/modules/recurrences/adapters/db/unit_of_work.py`
- Create: `app/modules/recurrences/adapters/db/factories.py`

- [ ] **Step 1: Escrever `adapters/db/repository.py`**

```python
# app/modules/recurrences/adapters/db/repository.py
import uuid
from datetime import date

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesRepository(BaseRepository[RecurrenceModel, Recurrence, RecurrenceFilters]):
    model = RecurrenceModel
    filters_type = RecurrenceFilters

    def _to_entity(self, row: RecurrenceModel) -> Recurrence:
        return Recurrence(
            id=row.id,
            client_id=row.client_id,
            description=row.description,
            amount=row.amount,
            day_of_month=row.day_of_month,
            start_date=row.start_date,
            end_date=row.end_date,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(
        self, stmt: sa.Select, filters: RecurrenceFilters
    ) -> sa.Select:
        if filters.client_id is not None:
            stmt = stmt.where(RecurrenceModel.client_id == filters.client_id)
        if filters.is_active is not None:
            stmt = stmt.where(RecurrenceModel.is_active == filters.is_active)
        return stmt

    async def get_active_due_in_range(
        self, from_date: date, to_date: date
    ) -> list[tuple[Recurrence, str]]:
        """Retorna recorrências ativas com client_name, filtradas pelo intervalo."""
        from app.modules.clients.adapters.db.models import Client as ClientModel

        stmt = (
            sa.select(RecurrenceModel, ClientModel.name)
            .join(ClientModel, RecurrenceModel.client_id == ClientModel.id)
            .where(RecurrenceModel.is_active == True)  # noqa: E712
            .where(RecurrenceModel.start_date <= to_date)
            .where(
                sa.or_(
                    RecurrenceModel.end_date.is_(None),
                    RecurrenceModel.end_date >= from_date,
                )
            )
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(self._to_entity(row[0]), row[1]) for row in rows]
```

- [ ] **Step 2: Escrever `adapters/db/unit_of_work.py`**

```python
# app/modules/recurrences/adapters/db/unit_of_work.py
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.recurrences.adapters.db.repository import RecurrencesRepository


class RecurrencesUnitOfWork(BaseUnitOfWork):
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        super().__init__(session_factory=session_factory)
        self._recurrences: RecurrencesRepository | None = None

    @property
    def recurrences(self) -> RecurrencesRepository:
        if self._recurrences is None:
            raise RuntimeError("Repositório de recorrências não inicializado.")
        return self._recurrences

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._recurrences = RecurrencesRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._recurrences = None
```

- [ ] **Step 3: Escrever `adapters/db/factories.py`**

```python
# app/modules/recurrences/adapters/db/factories.py
from app.core.db.session import db
from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork


def make_unit_of_work() -> RecurrencesUnitOfWork:
    return RecurrencesUnitOfWork(session_factory=db.create_session)
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/recurrences/adapters/db/
git commit -m "feat(recurrences): DB repository e unit of work"
```

---

### Task 7: HTTP adapter — schemas, dependencies e router

**Files:**
- Create: `app/modules/recurrences/adapters/http/schemas.py`
- Create: `app/modules/recurrences/adapters/http/dependencies.py`
- Create: `app/modules/recurrences/adapters/http/router.py`
- Create: `app/modules/recurrences/adapters/http/__init__.py`

- [ ] **Step 1: Escrever `adapters/http/schemas.py`**

```python
# app/modules/recurrences/adapters/http/schemas.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class RecurrenceCreate(BaseModel):
    client_id: uuid.UUID
    description: Annotated[str, Field(max_length=1000, min_length=1)]
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    day_of_month: Annotated[int, Field(ge=1, le=31)]
    start_date: date
    end_date: date | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_end_date(self) -> "RecurrenceCreate":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date deve ser maior ou igual a start_date.")
        return self


class RecurrenceUpdate(BaseModel):
    client_id: uuid.UUID | None = None
    description: Annotated[str | None, Field(max_length=1000, min_length=1)] = None
    amount: Annotated[Decimal | None, Field(gt=0, decimal_places=2)] = None
    day_of_month: Annotated[int | None, Field(ge=1, le=31)] = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None


class RecurrenceRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    client_name: str = ""
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpcomingItemRead(BaseModel):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    amount: Decimal
    description: str
    scheduled_date: date


class RecurrencesPaginationFilters(BaseModel):
    client_id: uuid.UUID | None = None
    is_active: bool | None = None
```

- [ ] **Step 2: Escrever `adapters/http/dependencies.py`**

```python
# app/modules/recurrences/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.recurrences.adapters.db.factories import make_unit_of_work
from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork
from app.modules.recurrences.adapters.http.schemas import RecurrencesPaginationFilters
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters

RecurrencesUnitOfWorkDep = Annotated[RecurrencesUnitOfWork, Depends(make_unit_of_work)]


def get_pagination_filters(
    query_params: Annotated[RecurrencesPaginationFilters, Depends()],
) -> RecurrenceFilters:
    return RecurrenceFilters(
        client_id=query_params.client_id,
        is_active=query_params.is_active,
    )


PaginationFiltersDep = Annotated[RecurrenceFilters, Depends(get_pagination_filters)]
```

- [ ] **Step 3: Escrever `adapters/http/router.py`**

```python
# app/modules/recurrences/adapters/http/router.py
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ValidationAppError
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.recurrences.adapters.http.dependencies import (
    PaginationFiltersDep,
    RecurrencesUnitOfWorkDep,
)
from app.modules.recurrences.adapters.http.schemas import (
    RecurrenceCreate,
    RecurrenceRead,
    RecurrenceUpdate,
    UpcomingItemRead,
)
from app.modules.recurrences.application.dtos.commands import (
    CreateRecurrenceCommand,
    UpdateRecurrenceCommand,
)
from app.modules.recurrences.application.use_cases.recurrences_creator import (
    RecurrencesCreator,
)
from app.modules.recurrences.application.use_cases.recurrences_paginator import (
    RecurrencesPaginator,
)
from app.modules.recurrences.application.use_cases.recurrences_reader import (
    RecurrencesReader,
)
from app.modules.recurrences.application.use_cases.recurrences_updater import (
    RecurrencesUpdater,
)
from app.modules.recurrences.application.use_cases.upcoming_reader import UpcomingReader
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("/upcoming", response_model=list[UpcomingItemRead])
async def get_upcoming(
    uow: RecurrencesUnitOfWorkDep,
    from_date: date = Query(..., alias="from"),
    to_date: date = Query(..., alias="to"),
) -> list[UpcomingItemRead]:
    if (to_date - from_date).days > 90:
        raise ValidationAppError("Intervalo máximo é de 90 dias.")
    reader = UpcomingReader(uow=uow)
    items = await reader.list_upcoming(from_date, to_date)
    return [UpcomingItemRead(**vars(item)) for item in items]


@router.get("", response_model=PaginatedResponse[RecurrenceRead])
async def list_recurrences(
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: RecurrencesUnitOfWorkDep,
) -> PaginatedResponse[RecurrenceRead]:
    paginator = RecurrencesPaginator(uow=uow)
    page = await paginator.paginate(page_params=page_params, filters=filters)
    return build_paginated_response(
        items=[RecurrenceRead.model_validate(r.to_dict()) for r in page.items],
        total=page.total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.post("", response_model=RecurrenceRead, status_code=201)
async def create_recurrence(
    data: RecurrenceCreate,
    uow: RecurrencesUnitOfWorkDep,
) -> RecurrenceRead:
    creator = RecurrencesCreator(uow=uow)
    rec = await creator.create(
        CreateRecurrenceCommand(**data.model_dump(exclude_unset=True))
    )
    return RecurrenceRead.model_validate(rec.to_dict())


@router.get("/{recurrence_id}", response_model=RecurrenceRead)
async def get_recurrence(
    recurrence_id: uuid.UUID,
    uow: RecurrencesUnitOfWorkDep,
) -> RecurrenceRead:
    reader = RecurrencesReader(uow=uow)
    rec = await reader.get_by_id(recurrence_id)
    return RecurrenceRead.model_validate(rec.to_dict())


@router.patch("/{recurrence_id}", response_model=RecurrenceRead)
async def update_recurrence(
    recurrence_id: uuid.UUID,
    data: RecurrenceUpdate,
    uow: RecurrencesUnitOfWorkDep,
) -> RecurrenceRead:
    updater = RecurrencesUpdater(uow=uow)
    rec = await updater.update(
        recurrence_id,
        UpdateRecurrenceCommand(**data.model_dump(exclude_unset=True)),
    )
    return RecurrenceRead.model_validate(rec.to_dict())
```

**Nota:** `ValidationAppError` está em `app/core/exceptions.py` com `status_code=422`.

- [ ] **Step 4: Criar `__init__.py`**

```bash
touch app/modules/recurrences/adapters/http/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add app/modules/recurrences/adapters/http/
git commit -m "feat(recurrences): HTTP router, schemas e dependencies"
```

---

### Task 8: Registrar no router principal e migrations/env.py

**Files:**
- Modify: `app/api/router.py`
- Modify: `migrations/env.py`

- [ ] **Step 1: Atualizar `app/api/router.py`**

Adicionar import:
```python
from app.modules.recurrences.adapters.http.router import router as recurrences_router
```

Adicionar inside `build_api_router()`:
```python
router.include_router(recurrences_router, prefix="/recurrences", tags=["Recorrências"])
```

- [ ] **Step 2: Atualizar `migrations/env.py`**

Adicionar após o import de clients models:
```python
import app.modules.recurrences.adapters.db.models  # noqa: F401
```

- [ ] **Step 3: Commit**

```bash
git add app/api/router.py migrations/env.py
git commit -m "feat(recurrences): registrar router e model no alembic"
```

---

### Task 9: Migration Alembic

- [ ] **Step 1: Gerar a migration**

```bash
uv run alembic revision --autogenerate -m "add_recurrences_table"
```

Verificar no arquivo gerado:
- Tabela `recurrences` com todos os campos
- FK `client_id → clients.id` com `ondelete="RESTRICT"`
- Índice em `client_id`
- Índice composto em `(is_active, day_of_month)`

- [ ] **Step 2: Aplicar**

```bash
uv run alembic upgrade head
```

- [ ] **Step 3: Commit**

```bash
git add migrations/versions/
git commit -m "feat(recurrences): migration tabela recurrences"
```

---

### Task 10: Integration tests

**Files:**
- Create: `tests/integration/modules/recurrences/conftest.py`
- Create: `tests/integration/modules/recurrences/test_recurrences.py`

- [ ] **Step 1: Escrever `conftest.py`**

```python
# tests/integration/modules/recurrences/conftest.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel


async def insert_client(conn: AsyncConnection, document: str = "12345678901") -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(ClientModel).values(
            id=uid, document=document, name="Cliente Teste",
            municipal_registration=None, phone=None, email=None,
            zip_code=None, street=None, number=None, complement=None,
            neighborhood=None, ibge_city_code=None, is_active=True,
            created_at=now, updated_at=now,
        )
    )
    return uid


async def insert_recurrence(
    conn: AsyncConnection,
    client_id: uuid.UUID,
    *,
    day_of_month: int = 15,
    is_active: bool = True,
    end_date: date | None = None,
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(RecurrenceModel).values(
            id=uid,
            client_id=client_id,
            description="Serviço mensal",
            amount=Decimal("1500.00"),
            day_of_month=day_of_month,
            start_date=date(2026, 1, 1),
            end_date=end_date,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_client_id(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_client(db_connection)


@pytest.fixture
async def test_recurrence_id(
    db_connection: AsyncConnection, test_client_id: uuid.UUID
) -> uuid.UUID:
    return await insert_recurrence(db_connection, test_client_id)
```

- [ ] **Step 2: Atualizar `tests/integration/conftest.py`**

Adicionar o override do UoW de recorrências no fixture `client`:

```python
from app.modules.recurrences.adapters.db.factories import make_unit_of_work as make_recurrences_uow
from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork

def make_test_recurrences_uow() -> RecurrencesUnitOfWork:
    return RecurrencesUnitOfWork(session_factory=test_session_factory)

app.dependency_overrides[make_recurrences_uow] = make_test_recurrences_uow
```

- [ ] **Step 3: Escrever `test_recurrences.py`**

```python
# tests/integration/modules/recurrences/test_recurrences.py
import uuid
from datetime import date

import pytest
from httpx import AsyncClient


async def test_create_recurrence(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.post(
        "/recurrences",
        json={
            "client_id": str(test_client_id),
            "description": "Assessoria mensal",
            "amount": "1500.00",
            "day_of_month": 15,
            "start_date": "2026-01-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_id"] == str(test_client_id)
    assert data["day_of_month"] == 15


async def test_create_recurrence_client_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.post(
        "/recurrences",
        json={
            "client_id": str(uuid.uuid4()),
            "description": "X",
            "amount": "100.00",
            "day_of_month": 1,
            "start_date": "2026-01-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_get_recurrence(
    client: AsyncClient, auth_headers: dict, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.get(f"/recurrences/{test_recurrence_id}", headers=auth_headers)
    assert resp.status_code == 200


async def test_list_recurrences_filter_active(
    client: AsyncClient, auth_headers: dict, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.get("/recurrences?is_active=true", headers=auth_headers)
    assert resp.status_code == 200
    ids = [i["id"] for i in resp.json()["items"]]
    assert str(test_recurrence_id) in ids


async def test_list_recurrences_filter_client(
    client: AsyncClient, auth_headers: dict,
    test_client_id: uuid.UUID, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.get(
        f"/recurrences?client_id={test_client_id}", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_update_recurrence(
    client: AsyncClient, auth_headers: dict, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.patch(
        f"/recurrences/{test_recurrence_id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


async def test_no_delete_endpoint(
    client: AsyncClient, auth_headers: dict, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.delete(f"/recurrences/{test_recurrence_id}", headers=auth_headers)
    assert resp.status_code == 405


async def test_delete_client_with_recurrence_returns_409(
    client: AsyncClient, auth_headers: dict,
    test_client_id: uuid.UUID, test_recurrence_id: uuid.UUID
) -> None:
    resp = await client.delete(f"/clients/{test_client_id}", headers=auth_headers)
    assert resp.status_code == 409


async def test_upcoming_day_31_february(
    client: AsyncClient, auth_headers: dict, db_connection, test_client_id: uuid.UUID
) -> None:
    from tests.integration.modules.recurrences.conftest import insert_recurrence
    await insert_recurrence(db_connection, test_client_id, day_of_month=31)

    resp = await client.get(
        "/recurrences/upcoming?from=2026-02-01&to=2026-02-28",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    dates = [i["scheduled_date"] for i in items]
    assert "2026-02-28" in dates


async def test_upcoming_expired_end_date(
    client: AsyncClient, auth_headers: dict, db_connection, test_client_id: uuid.UUID
) -> None:
    from tests.integration.modules.recurrences.conftest import insert_recurrence
    from datetime import date as d
    await insert_recurrence(
        db_connection, test_client_id,
        day_of_month=15, end_date=d(2026, 5, 31)
    )
    resp = await client.get(
        "/recurrences/upcoming?from=2026-06-01&to=2026-06-30",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = [i for i in resp.json() if i["scheduled_date"] == "2026-06-15"]
    assert len(items) == 0


async def test_upcoming_interval_too_large(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get(
        "/recurrences/upcoming?from=2026-01-01&to=2026-04-10",
        headers=auth_headers,
    )
    assert resp.status_code == 422
```

- [ ] **Step 4: Rodar os testes**

```bash
uv run pytest tests/integration/modules/recurrences/ -v
```

Esperado: todos passam.

- [ ] **Step 5: Commit final**

```bash
git add tests/integration/modules/recurrences/
git commit -m "test(recurrences): integration tests CRUD e upcoming"
```

---

## Verificação final

- [ ] Lint: `uv run ruff check app/modules/recurrences/`
- [ ] Type check: `uv run mypy app/modules/recurrences/`
- [ ] Todos os testes: `uv run pytest tests/ -v`

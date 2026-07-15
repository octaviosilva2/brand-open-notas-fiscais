# Notas Fiscais API — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Pré-requisito:** Planos `2026-06-14-clientes-api.md`, `2026-06-14-recorrencias-api.md` e `2026-06-14-betha-integration.md` devem estar **completos e mergeados**.

**Goal:** Implementar o módulo de histórico de notas fiscais geradas (`invoices`): listagem com filtros, download de XML/PDF e reprocessamento síncrono de falhas.

**Architecture:** Slice hexagonal em `app/modules/invoices/`. A entidade `Invoice` é criada pelo Agendador (próximo plano) e consultada/reprocessada por este módulo. O retry é **síncrono** — o endpoint aguarda o resultado completo do `DpsPoller`. Unique constraint em `(recurrence_id, scheduled_date)` garante idempotência. `client_name` é obtido via join para evitar N+1.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, PostgreSQL, Pydantic v2, Alembic, pytest-asyncio, httpx.

---

## Estrutura de arquivos

**Criar:**
- `app/modules/invoices/__init__.py`
- `app/modules/invoices/domain/__init__.py`
- `app/modules/invoices/domain/entities.py`
- `app/modules/invoices/application/__init__.py`
- `app/modules/invoices/application/ports/__init__.py`
- `app/modules/invoices/application/ports/repository.py`
- `app/modules/invoices/application/ports/unit_of_work.py`
- `app/modules/invoices/application/dtos/__init__.py`
- `app/modules/invoices/application/dtos/commands.py`
- `app/modules/invoices/application/dtos/filters.py`
- `app/modules/invoices/application/use_cases/__init__.py`
- `app/modules/invoices/application/use_cases/invoices_reader.py`
- `app/modules/invoices/application/use_cases/invoice_retryer.py`
- `app/modules/invoices/adapters/__init__.py`
- `app/modules/invoices/adapters/db/__init__.py`
- `app/modules/invoices/adapters/db/models.py`
- `app/modules/invoices/adapters/db/repository.py`
- `app/modules/invoices/adapters/db/unit_of_work.py`
- `app/modules/invoices/adapters/db/factories.py`
- `app/modules/invoices/adapters/http/__init__.py`
- `app/modules/invoices/adapters/http/schemas.py`
- `app/modules/invoices/adapters/http/dependencies.py`
- `app/modules/invoices/adapters/http/router.py`
- `tests/unit/modules/invoices/__init__.py`
- `tests/unit/modules/invoices/test_retry_logic.py`
- `tests/integration/modules/invoices/__init__.py`
- `tests/integration/modules/invoices/conftest.py`
- `tests/integration/modules/invoices/test_invoices.py`

**Modificar:**
- `app/api/router.py` — registrar router de invoices
- `migrations/env.py` — importar `InvoiceModel`

---

### Task 1: Domain entities

**Files:**
- Create: `app/modules/invoices/domain/entities.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/invoices/__init__.py app/modules/invoices/domain/__init__.py
```

- [ ] **Step 2: Escrever `domain/entities.py`**

```python
# app/modules/invoices/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset

InvoiceStatus = Literal["pending", "processing", "success", "error"]


@dataclass(frozen=True, slots=True)
class NewInvoice(BaseCreateCommand):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: str = "pending"
    n_dps: int | None = None
    protocol: str | None = None
    nf_number: str | None = None
    pdf_url: str | None = None
    xml_sent: str | None = None
    xml_response: str | None = None
    error_message: str | None = None
    emission_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class UpdateInvoice(BaseUpdateCommand):
    status: str | Unset = UNSET
    n_dps: int | None | Unset = UNSET
    protocol: str | None | Unset = UNSET
    nf_number: str | None | Unset = UNSET
    pdf_url: str | None | Unset = UNSET
    xml_sent: str | None | Unset = UNSET
    xml_response: str | None | Unset = UNSET
    error_message: str | None | Unset = UNSET
    emission_date: datetime | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Invoice:
    id: uuid.UUID
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: str
    n_dps: int | None
    protocol: str | None
    nf_number: str | None
    pdf_url: str | None
    xml_sent: str | None
    xml_response: str | None
    error_message: str | None
    emission_date: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self, client_name: str = "") -> dict[str, Any]:
        return {
            "id": self.id,
            "recurrence_id": self.recurrence_id,
            "client_id": self.client_id,
            "client_name": client_name,
            "scheduled_date": self.scheduled_date,
            "amount": self.amount,
            "description": self.description,
            "status": self.status,
            "n_dps": self.n_dps,
            "protocol": self.protocol,
            "nf_number": self.nf_number,
            "pdf_url": self.pdf_url,
            "xml_sent": self.xml_sent,
            "xml_response": self.xml_response,
            "error_message": self.error_message,
            "emission_date": self.emission_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/invoices/
git commit -m "feat(invoices): domain entities"
```

---

### Task 2: Application ports e DTOs

**Files:**
- Create: `app/modules/invoices/application/ports/repository.py`
- Create: `app/modules/invoices/application/ports/unit_of_work.py`
- Create: `app/modules/invoices/application/dtos/commands.py`
- Create: `app/modules/invoices/application/dtos/filters.py`

- [ ] **Step 1: Escrever `ports/repository.py`**

```python
# app/modules/invoices/application/ports/repository.py
import uuid
from datetime import date
from typing import Protocol

from app.modules.invoices.domain.entities import Invoice, NewInvoice, UpdateInvoice


class InvoicesRepositoryProtocol(Protocol):
    async def get_by_id(self, id_: uuid.UUID) -> Invoice: ...
    async def get_by_id_or_none(self, id_: uuid.UUID) -> Invoice | None: ...
    async def get_with_client_name(self, id_: uuid.UUID) -> tuple[Invoice, str]: ...
    async def create(self, create_command: NewInvoice) -> Invoice: ...
    async def update(self, id_: uuid.UUID, update_command: UpdateInvoice) -> Invoice: ...
    async def get_by_recurrence_and_date(
        self, recurrence_id: uuid.UUID, scheduled_date: date
    ) -> Invoice | None: ...
```

- [ ] **Step 2: Escrever `ports/unit_of_work.py`**

```python
# app/modules/invoices/application/ports/unit_of_work.py
from types import TracebackType
from typing import Protocol, Self

from app.modules.invoices.application.ports.repository import InvoicesRepositoryProtocol


class InvoicesUnitOfWorkProtocol(Protocol):
    @property
    def invoices(self) -> InvoicesRepositoryProtocol: ...

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
# app/modules/invoices/application/dtos/commands.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateInvoiceCommand(BaseCreateCommand):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: str = "pending"


@dataclass(frozen=True, slots=True)
class UpdateInvoiceCommand(BaseUpdateCommand):
    status: str | Unset = UNSET
    n_dps: int | None | Unset = UNSET
    protocol: str | None | Unset = UNSET
    nf_number: str | None | Unset = UNSET
    pdf_url: str | None | Unset = UNSET
    xml_sent: str | None | Unset = UNSET
    xml_response: str | None | Unset = UNSET
    error_message: str | None | Unset = UNSET
    emission_date: datetime | None | Unset = UNSET
```

- [ ] **Step 4: Escrever `dtos/filters.py`**

```python
# app/modules/invoices/application/dtos/filters.py
import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class InvoiceFilters:
    status: str | None = None
    client_id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
```

- [ ] **Step 5: Criar `__init__.py`s**

```bash
touch app/modules/invoices/application/__init__.py
touch app/modules/invoices/application/ports/__init__.py
touch app/modules/invoices/application/dtos/__init__.py
touch app/modules/invoices/application/use_cases/__init__.py
```

- [ ] **Step 6: Commit**

```bash
git add app/modules/invoices/application/
git commit -m "feat(invoices): ports e DTOs"
```

---

### Task 3: DB adapter — model

**Files:**
- Create: `app/modules/invoices/adapters/db/models.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/invoices/adapters/__init__.py app/modules/invoices/adapters/db/__init__.py
```

- [ ] **Step 2: Escrever `adapters/db/models.py`**

```python
# app/modules/invoices/adapters/db/models.py
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    recurrence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recurrences.id", ondelete="RESTRICT"),
        nullable=False,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    n_dps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nf_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    xml_sent: Mapped[str | None] = mapped_column(Text, nullable=True)
    xml_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    emission_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
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
        UniqueConstraint("recurrence_id", "scheduled_date", name="uq_invoice_recurrence_date"),
        Index("ix_invoices_status_scheduled_date", "status", "scheduled_date"),
        Index("ix_invoices_client_id", "client_id"),
    )
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/invoices/adapters/db/models.py app/modules/invoices/adapters/__init__.py app/modules/invoices/adapters/db/__init__.py
git commit -m "feat(invoices): SQLAlchemy model"
```

---

### Task 4: DB adapter — repository, UoW e factories

**Files:**
- Create: `app/modules/invoices/adapters/db/repository.py`
- Create: `app/modules/invoices/adapters/db/unit_of_work.py`
- Create: `app/modules/invoices/adapters/db/factories.py`

- [ ] **Step 1: Escrever `adapters/db/repository.py`**

```python
# app/modules/invoices/adapters/db/repository.py
import uuid
from datetime import date

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.invoices.adapters.db.models import Invoice as InvoiceModel
from app.modules.invoices.application.dtos.filters import InvoiceFilters
from app.modules.invoices.domain.entities import Invoice


class InvoicesRepository(BaseRepository[InvoiceModel, Invoice, InvoiceFilters]):
    model = InvoiceModel
    filters_type = InvoiceFilters

    def _to_entity(self, row: InvoiceModel) -> Invoice:
        return Invoice(
            id=row.id,
            recurrence_id=row.recurrence_id,
            client_id=row.client_id,
            scheduled_date=row.scheduled_date,
            amount=row.amount,
            description=row.description,
            status=row.status,
            n_dps=row.n_dps,
            protocol=row.protocol,
            nf_number=row.nf_number,
            pdf_url=row.pdf_url,
            xml_sent=row.xml_sent,
            xml_response=row.xml_response,
            error_message=row.error_message,
            emission_date=row.emission_date,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: InvoiceFilters) -> sa.Select:
        if filters.status:
            stmt = stmt.where(InvoiceModel.status == filters.status)
        if filters.client_id:
            stmt = stmt.where(InvoiceModel.client_id == filters.client_id)
        if filters.from_date:
            stmt = stmt.where(InvoiceModel.scheduled_date >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(InvoiceModel.scheduled_date <= filters.to_date)
        return stmt.order_by(
            InvoiceModel.scheduled_date.desc(), InvoiceModel.created_at.desc()
        )

    async def get_with_client_name(self, id_: uuid.UUID) -> tuple[Invoice, str]:
        stmt = (
            sa.select(InvoiceModel, ClientModel.name)
            .join(ClientModel, InvoiceModel.client_id == ClientModel.id)
            .where(InvoiceModel.id == id_)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(f"Invoice com ID {id_} não encontrado.")
        return self._to_entity(row[0]), row[1]

    async def get_by_recurrence_and_date(
        self, recurrence_id: uuid.UUID, scheduled_date: date
    ) -> Invoice | None:
        result = await self._session.execute(
            sa.select(InvoiceModel).where(
                InvoiceModel.recurrence_id == recurrence_id,
                InvoiceModel.scheduled_date == scheduled_date,
            )
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def paginate_with_client_name(
        self, filters: InvoiceFilters, page: int, page_size: int
    ) -> tuple[list[tuple[Invoice, str]], int]:
        stmt = (
            sa.select(InvoiceModel, ClientModel.name)
            .join(ClientModel, InvoiceModel.client_id == ClientModel.id)
        )
        if filters.status:
            stmt = stmt.where(InvoiceModel.status == filters.status)
        if filters.client_id:
            stmt = stmt.where(InvoiceModel.client_id == filters.client_id)
        if filters.from_date:
            stmt = stmt.where(InvoiceModel.scheduled_date >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(InvoiceModel.scheduled_date <= filters.to_date)

        stmt = stmt.order_by(
            InvoiceModel.scheduled_date.desc(), InvoiceModel.created_at.desc()
        )

        count_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt) or 0

        result = await self._session.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
        rows = result.all()
        return [(self._to_entity(r[0]), r[1]) for r in rows], total
```

- [ ] **Step 2: Escrever `adapters/db/unit_of_work.py`**

```python
# app/modules/invoices/adapters/db/unit_of_work.py
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.invoices.adapters.db.repository import InvoicesRepository


class InvoicesUnitOfWork(BaseUnitOfWork):
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        super().__init__(session_factory=session_factory)
        self._invoices: InvoicesRepository | None = None

    @property
    def invoices(self) -> InvoicesRepository:
        if self._invoices is None:
            raise RuntimeError("Repositório de invoices não inicializado.")
        return self._invoices

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._invoices = InvoicesRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._invoices = None
```

- [ ] **Step 3: Escrever `adapters/db/factories.py`**

```python
# app/modules/invoices/adapters/db/factories.py
from app.core.db.session import db
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork


def make_unit_of_work() -> InvoicesUnitOfWork:
    return InvoicesUnitOfWork(session_factory=db.create_session)
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/invoices/adapters/db/
git commit -m "feat(invoices): DB repository e unit of work"
```

---

### Task 5: Application use cases

**Files:**
- Create: `app/modules/invoices/application/use_cases/invoices_reader.py`
- Create: `app/modules/invoices/application/use_cases/invoice_retryer.py`

- [ ] **Step 1: Escrever `invoices_reader.py`**

```python
# app/modules/invoices/application/use_cases/invoices_reader.py
import uuid
from datetime import date, timedelta

from app.modules.invoices.application.dtos.filters import InvoiceFilters
from app.modules.invoices.application.ports.unit_of_work import InvoicesUnitOfWorkProtocol
from app.modules.invoices.domain.entities import Invoice
from app.core.pagination.params import PageParams


class InvoicesReader:
    def __init__(self, uow: InvoicesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(self, id_: uuid.UUID) -> tuple[Invoice, str]:
        async with self._uow as uow:
            return await uow.invoices.get_with_client_name(id_)

    async def list_paginated(
        self,
        filters: InvoiceFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Invoice, str]], int]:
        today = date.today()
        effective_from = filters.from_date or (today - timedelta(days=30))
        effective_to = filters.to_date or today
        effective_filters = InvoiceFilters(
            status=filters.status,
            client_id=filters.client_id,
            from_date=effective_from,
            to_date=effective_to,
        )
        async with self._uow as uow:
            return await uow.invoices.paginate_with_client_name(
                effective_filters, page, page_size
            )
```

- [ ] **Step 2: Escrever `invoice_retryer.py`**

```python
# app/modules/invoices/application/use_cases/invoice_retryer.py
import uuid
from datetime import UTC, datetime, timedelta

from app.core.exceptions import ConflictError
from app.core.settings import settings
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.poller import DpsPoller
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.invoices.application.dtos.commands import UpdateInvoiceCommand
from app.modules.invoices.application.ports.unit_of_work import InvoicesUnitOfWorkProtocol
from app.modules.invoices.domain.entities import Invoice
from app.modules.recurrences.adapters.db.factories import (
    make_unit_of_work as make_recurrences_uow,
)


class InvoiceRetryer:
    def __init__(
        self,
        uow: InvoicesUnitOfWorkProtocol,
        poller: DpsPoller | None = None,
        clients_uow_factory=None,
        recurrences_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._poller = poller or DpsPoller()
        self._clients_uow_factory = clients_uow_factory or make_clients_uow
        self._recurrences_uow_factory = recurrences_uow_factory or make_recurrences_uow

    async def retry(self, invoice_id: uuid.UUID) -> tuple[Invoice, str]:
        async with self._uow as uow:
            invoice, client_name = await uow.invoices.get_with_client_name(invoice_id)
            self._validate_retryable(invoice)

            # Limpa e redefine como pending
            await uow.invoices.update(
                invoice_id,
                UpdateInvoiceCommand(
                    status="pending",
                    protocol=None,
                    nf_number=None,
                    pdf_url=None,
                    xml_sent=None,
                    xml_response=None,
                    error_message=None,
                    emission_date=None,
                ),
            )

            # Busca n_dps novo
            n_dps = await next_n_dps(uow.session, settings.BETHA_SERIE)  # type: ignore[attr-defined]

        # Busca client e recurrence para montar payload
        clients_uow = self._clients_uow_factory()
        async with clients_uow as cuow:
            client = await cuow.clients.get_by_id(invoice.client_id)

        recurrences_uow = self._recurrences_uow_factory()
        async with recurrences_uow as ruow:
            recurrence = await ruow.recurrences.get_by_id(invoice.recurrence_id)

        payload = DpsPayload(
            recurrence_id=invoice.recurrence_id,
            client=client,
            recurrence=recurrence,
            emission_date=invoice.scheduled_date,
            n_dps=n_dps,
        )

        result: EmissionResult = await self._poller.emit_and_poll(payload)

        now = datetime.now(UTC)
        async with self._uow as uow:
            updated = await uow.invoices.update(
                invoice_id,
                UpdateInvoiceCommand(
                    status="success" if result.ok else "error",
                    n_dps=n_dps,
                    protocol=result.protocol,
                    nf_number=result.nf_number,
                    pdf_url=result.pdf_url,
                    xml_sent=result.xml_sent or None,
                    xml_response=result.xml_response or None,
                    error_message=result.error_message,
                    emission_date=now if result.ok else None,
                ),
            )
            _, client_name = await uow.invoices.get_with_client_name(invoice_id)

        return updated, client_name

    def _validate_retryable(self, invoice: Invoice) -> None:
        if invoice.status == "error":
            return
        if invoice.status == "processing":
            staleness_threshold = datetime.now(UTC) - timedelta(minutes=10)
            if invoice.updated_at < staleness_threshold:
                return
        raise ConflictError(
            "Esta nota não está disponível para reprocessamento."
        )
```

**Nota importante:** `uow.session` precisa ser exposto publicamente na `InvoicesUnitOfWork`. Verificar se `BaseUnitOfWork` expõe `session`. Se não, adicionar `@property session` que retorna `self._session` à classe `InvoicesUnitOfWork`.

- [ ] **Step 3: Verificar que `BaseUnitOfWork` expõe `session`**

```bash
grep -n "session" app/core/db/unit_of_work.py
```

Se não tiver `@property def session`, adicionar em `InvoicesUnitOfWork`:
```python
@property
def session(self) -> AsyncSession:
    return self._session
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/invoices/application/use_cases/
git commit -m "feat(invoices): use cases reader e retryer"
```

---

### Task 6: HTTP adapter — schemas, dependencies e router

**Files:**
- Create: `app/modules/invoices/adapters/http/schemas.py`
- Create: `app/modules/invoices/adapters/http/dependencies.py`
- Create: `app/modules/invoices/adapters/http/router.py`
- Create: `app/modules/invoices/adapters/http/__init__.py`

- [ ] **Step 1: Escrever `adapters/http/schemas.py`**

```python
# app/modules/invoices/adapters/http/schemas.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class InvoiceRead(BaseModel):
    id: uuid.UUID
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
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

    model_config = {"from_attributes": True}


class InvoiceDetailRead(InvoiceRead):
    """InvoiceRead com campos xml (apenas para GET /invoices/{id})."""
    xml_sent: str | None
    xml_response: str | None


class InvoicesPaginationFilters(BaseModel):
    status: str | None = None
    client_id: uuid.UUID | None = None
    from_date: date | None = Field(None, alias="from")
    to_date: date | None = Field(None, alias="to")

    model_config = {"populate_by_name": True}
```

- [ ] **Step 2: Escrever `adapters/http/dependencies.py`**

```python
# app/modules/invoices/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.invoices.adapters.db.factories import make_unit_of_work
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork
from app.modules.invoices.adapters.http.schemas import InvoicesPaginationFilters
from app.modules.invoices.application.dtos.filters import InvoiceFilters

InvoicesUnitOfWorkDep = Annotated[InvoicesUnitOfWork, Depends(make_unit_of_work)]


def get_invoice_filters(
    query_params: Annotated[InvoicesPaginationFilters, Depends()],
) -> InvoiceFilters:
    return InvoiceFilters(
        status=query_params.status,
        client_id=query_params.client_id,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
    )


InvoiceFiltersDep = Annotated[InvoiceFilters, Depends(get_invoice_filters)]
```

- [ ] **Step 3: Escrever `adapters/http/router.py`**

```python
# app/modules/invoices/adapters/http/router.py
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, Response

from app.core.exceptions import NotFoundError
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.invoices.adapters.http.dependencies import (
    InvoiceFiltersDep,
    InvoicesUnitOfWorkDep,
)
from app.modules.invoices.adapters.http.schemas import (
    InvoiceDetailRead,
    InvoiceRead,
)
from app.modules.invoices.application.use_cases.invoice_retryer import InvoiceRetryer
from app.modules.invoices.application.use_cases.invoices_reader import InvoicesReader
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("", response_model=PaginatedResponse[InvoiceRead])
async def list_invoices(
    filters: InvoiceFiltersDep,
    uow: InvoicesUnitOfWorkDep,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[InvoiceRead]:
    reader = InvoicesReader(uow=uow)
    items, total = await reader.list_paginated(filters, page, page_size)
    return build_paginated_response(
        items=[InvoiceRead.model_validate(inv.to_dict(cn)) for inv, cn in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> InvoiceDetailRead:
    reader = InvoicesReader(uow=uow)
    invoice, client_name = await reader.get_by_id(invoice_id)
    return InvoiceDetailRead.model_validate(invoice.to_dict(client_name))


@router.get("/{invoice_id}/xml")
async def get_invoice_xml(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> Response:
    reader = InvoicesReader(uow=uow)
    invoice, _ = await reader.get_by_id(invoice_id)
    if not invoice.xml_sent:
        raise NotFoundError("XML não disponível para esta nota.")
    filename = f"dps_{invoice.n_dps or invoice_id}.xml"
    return Response(
        content=invoice.xml_sent,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> RedirectResponse:
    reader = InvoicesReader(uow=uow)
    invoice, _ = await reader.get_by_id(invoice_id)
    if not invoice.pdf_url:
        raise NotFoundError("PDF não disponível para esta nota.")
    return RedirectResponse(url=invoice.pdf_url, status_code=302)


@router.post("/{invoice_id}/retry", response_model=InvoiceRead)
async def retry_invoice(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> InvoiceRead:
    retryer = InvoiceRetryer(uow=uow)
    invoice, client_name = await retryer.retry(invoice_id)
    return InvoiceRead.model_validate(invoice.to_dict(client_name))
```

- [ ] **Step 4: Criar `__init__.py`**

```bash
touch app/modules/invoices/adapters/http/__init__.py
```

- [ ] **Step 5: Commit**

```bash
git add app/modules/invoices/adapters/http/
git commit -m "feat(invoices): HTTP router, schemas e dependencies"
```

---

### Task 7: Registrar no router principal e migration

**Files:**
- Modify: `app/api/router.py`
- Modify: `migrations/env.py`

- [ ] **Step 1: Atualizar `app/api/router.py`**

```python
from app.modules.invoices.adapters.http.router import router as invoices_router
# e dentro de build_api_router():
router.include_router(invoices_router, prefix="/invoices", tags=["Notas Fiscais"])
```

- [ ] **Step 2: Atualizar `migrations/env.py`**

```python
import app.modules.invoices.adapters.db.models  # noqa: F401
```

- [ ] **Step 3: Gerar e aplicar migration**

```bash
uv run alembic revision --autogenerate -m "add_invoices_table"
uv run alembic upgrade head
```

Verificar:
- Tabela `invoices` com todos os campos
- FK `recurrence_id → recurrences.id` ON DELETE RESTRICT
- FK `client_id → clients.id` ON DELETE RESTRICT
- UNIQUE `(recurrence_id, scheduled_date)`
- Índice `(status, scheduled_date)`
- Índice `client_id`

- [ ] **Step 4: Commit**

```bash
git add app/api/router.py migrations/env.py migrations/versions/
git commit -m "feat(invoices): registrar router, model e migration"
```

---

### Task 8: Unit tests — lógica de retry

**Files:**
- Create: `tests/unit/modules/invoices/test_retry_logic.py`

- [ ] **Step 1: Escrever os testes**

```python
# tests/unit/modules/invoices/test_retry_logic.py
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.invoices.application.use_cases.invoice_retryer import InvoiceRetryer
from app.modules.invoices.domain.entities import Invoice
from app.core.exceptions import ConflictError


def _make_invoice(
    status: str,
    updated_at: datetime | None = None,
) -> Invoice:
    now = updated_at or datetime.now(UTC)
    return Invoice(
        id=uuid.uuid4(),
        recurrence_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        scheduled_date=date(2026, 6, 15),
        amount=Decimal("1500.00"),
        description="Serviço",
        status=status,
        n_dps=None,
        protocol=None,
        nf_number=None,
        pdf_url=None,
        xml_sent=None,
        xml_response=None,
        error_message=None,
        emission_date=None,
        created_at=now,
        updated_at=now,
    )


def _get_retryer() -> InvoiceRetryer:
    return InvoiceRetryer(uow=None)  # type: ignore[arg-type]


def test_validate_error_status_is_retryable():
    invoice = _make_invoice("error")
    retryer = _get_retryer()
    # Não lança exceção
    retryer._validate_retryable(invoice)


def test_validate_success_status_raises_conflict():
    invoice = _make_invoice("success")
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_pending_status_raises_conflict():
    invoice = _make_invoice("pending")
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_processing_recent_raises_conflict():
    recent = datetime.now(UTC) - timedelta(minutes=5)
    invoice = _make_invoice("processing", updated_at=recent)
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_processing_stale_is_retryable():
    stale = datetime.now(UTC) - timedelta(minutes=15)
    invoice = _make_invoice("processing", updated_at=stale)
    retryer = _get_retryer()
    # Não lança exceção
    retryer._validate_retryable(invoice)
```

- [ ] **Step 2: Rodar**

```bash
uv run pytest tests/unit/modules/invoices/ -v
```

Esperado: todos passam.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/modules/invoices/
git commit -m "test(invoices): unit tests lógica de retry"
```

---

### Task 9: Integration tests

**Files:**
- Create: `tests/integration/modules/invoices/conftest.py`
- Create: `tests/integration/modules/invoices/test_invoices.py`

- [ ] **Step 1: Escrever `conftest.py`**

```python
# tests/integration/modules/invoices/conftest.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.invoices.adapters.db.models import Invoice as InvoiceModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel


async def _insert_client(conn: AsyncConnection, document: str = "12345678901") -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(ClientModel).values(
            id=uid, document=document, name="Cliente NF",
            municipal_registration=None, phone=None, email=None,
            zip_code=None, street=None, number=None, complement=None,
            neighborhood=None, ibge_city_code=None, is_active=True,
            created_at=now, updated_at=now,
        )
    )
    return uid


async def _insert_recurrence(
    conn: AsyncConnection, client_id: uuid.UUID
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(RecurrenceModel).values(
            id=uid, client_id=client_id, description="Serviço",
            amount=Decimal("1500.00"), day_of_month=15,
            start_date=date(2026, 1, 1), end_date=None, is_active=True,
            created_at=now, updated_at=now,
        )
    )
    return uid


async def insert_invoice(
    conn: AsyncConnection,
    recurrence_id: uuid.UUID,
    client_id: uuid.UUID,
    *,
    status: str = "success",
    scheduled_date: date = date(2026, 6, 15),
    xml_sent: str | None = None,
    pdf_url: str | None = None,
    nf_number: str | None = "NF001",
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(InvoiceModel).values(
            id=uid, recurrence_id=recurrence_id, client_id=client_id,
            scheduled_date=scheduled_date, amount=Decimal("1500.00"),
            description="Serviço", status=status, n_dps=1,
            protocol="PROT001", nf_number=nf_number, pdf_url=pdf_url,
            xml_sent=xml_sent, xml_response=None, error_message=None,
            emission_date=now if status == "success" else None,
            created_at=now, updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_ids(db_connection: AsyncConnection) -> dict:
    client_id = await _insert_client(db_connection)
    rec_id = await _insert_recurrence(db_connection, client_id)
    inv_id = await insert_invoice(
        db_connection, rec_id, client_id,
        xml_sent="<xml>test</xml>",
        pdf_url="http://pdf.example.com/nf001.pdf",
    )
    return {"client_id": client_id, "recurrence_id": rec_id, "invoice_id": inv_id}
```

- [ ] **Step 2: Atualizar `tests/integration/conftest.py`**

Adicionar override para invoices UoW:

```python
from app.modules.invoices.adapters.db.factories import make_unit_of_work as make_invoices_uow
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork

def make_test_invoices_uow() -> InvoicesUnitOfWork:
    return InvoicesUnitOfWork(session_factory=test_session_factory)

app.dependency_overrides[make_invoices_uow] = make_test_invoices_uow
```

- [ ] **Step 3: Escrever `test_invoices.py`**

```python
# tests/integration/modules/invoices/test_invoices.py
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.integrations.betha.models import EmissionResult


async def test_list_invoices(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    resp = await client.get("/invoices", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1


async def test_list_invoices_filter_status(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    resp = await client.get("/invoices?status=success", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "success"


async def test_list_invoices_filter_client(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    cid = test_ids["client_id"]
    resp = await client.get(f"/invoices?client_id={cid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_invoice(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    iid = test_ids["invoice_id"]
    resp = await client.get(f"/invoices/{iid}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(iid)
    assert "xml_sent" in data


async def test_get_invoice_not_found(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get(f"/invoices/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_download_xml(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    iid = test_ids["invoice_id"]
    resp = await client.get(f"/invoices/{iid}/xml", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    assert "<xml>" in resp.text


async def test_download_xml_not_available(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )
    cid = await _insert_client(db_connection, document="88888888801")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(
        db_connection, rid, cid, xml_sent=None, nf_number=None
    )
    resp = await client.get(f"/invoices/{iid}/xml", headers=auth_headers)
    assert resp.status_code == 404


async def test_pdf_redirect(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    iid = test_ids["invoice_id"]
    resp = await client.get(
        f"/invoices/{iid}/pdf", headers=auth_headers, follow_redirects=False
    )
    assert resp.status_code == 302
    assert "pdf.example.com" in resp.headers["location"]


async def test_pdf_not_available(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )
    cid = await _insert_client(db_connection, document="77777777701")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(
        db_connection, rid, cid, pdf_url=None, nf_number=None
    )
    resp = await client.get(
        f"/invoices/{iid}/pdf", headers=auth_headers, follow_redirects=False
    )
    assert resp.status_code == 404


async def test_retry_success_invoice_returns_409(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    iid = test_ids["invoice_id"]
    resp = await client.post(f"/invoices/{iid}/retry", headers=auth_headers)
    assert resp.status_code == 409


async def test_retry_error_invoice(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )
    cid = await _insert_client(db_connection, document="66666666601")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(
        db_connection, rid, cid,
        status="error", nf_number=None, xml_sent="<xml/>"
    )

    mock_result = EmissionResult(
        ok=True, protocol="P1", nf_number="NF999", pdf_url="http://pdf/x"
    )
    mock_poller = MagicMock()
    mock_poller.emit_and_poll = AsyncMock(return_value=mock_result)

    with patch(
        "app.modules.invoices.application.use_cases.invoice_retryer.DpsPoller",
        return_value=mock_poller,
    ):
        resp = await client.post(f"/invoices/{iid}/retry", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["nf_number"] == "NF999"
```

- [ ] **Step 4: Rodar**

```bash
uv run pytest tests/integration/modules/invoices/ -v
```

Esperado: todos passam.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/modules/invoices/ tests/unit/modules/invoices/
git commit -m "test(invoices): integration tests e unit tests"
```

---

## Verificação final

- [ ] Lint: `uv run ruff check app/modules/invoices/`
- [ ] Type check: `uv run mypy app/modules/invoices/`
- [ ] Todos os testes: `uv run pytest tests/ -v`

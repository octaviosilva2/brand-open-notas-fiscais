# Agendador (Cron) — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Pré-requisito:** Todos os planos anteriores devem estar **completos e mergeados**: clientes, recorrências, betha integration e invoices.

**Goal:** Implementar o endpoint `POST /cron/run` que dispara as emissões diárias de NFS-e com idempotência, tolerância a falhas individuais, notificação por e-mail e suporte a cron automático no Docker.

**Architecture:** Módulo slim em `app/modules/cron/` com um use case `CronRunner` que orquestra recorrências → invoices → Betha. Autenticação dupla: JWT (usuário logado) ou `X-Cron-Secret` (docker cron). Notificação SMTP via `aiosmtplib`. Emissões sequenciais para garantir ordenação do `nDPS`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, aiosmtplib, pytest-asyncio, httpx.

---

## Estrutura de arquivos

**Criar:**
- `app/modules/cron/__init__.py`
- `app/modules/cron/application/__init__.py`
- `app/modules/cron/application/use_cases/__init__.py`
- `app/modules/cron/application/use_cases/cron_runner.py`
- `app/modules/cron/application/notification_service.py`
- `app/modules/cron/adapters/__init__.py`
- `app/modules/cron/adapters/http/__init__.py`
- `app/modules/cron/adapters/http/schemas.py`
- `app/modules/cron/adapters/http/dependencies.py`
- `app/modules/cron/adapters/http/router.py`
- `tests/unit/modules/cron/__init__.py`
- `tests/unit/modules/cron/test_cron_runner.py`
- `tests/unit/modules/cron/test_notification.py`
- `tests/integration/modules/cron/__init__.py`
- `tests/integration/modules/cron/conftest.py`
- `tests/integration/modules/cron/test_cron.py`

**Modificar:**
- `app/core/settings.py` — adicionar CRON_SECRET e SMTP_*
- `app/api/router.py` — registrar router do cron
- `docker-compose.yml` — adicionar serviço cron

---

### Task 1: Atualizar settings.py

**Files:**
- Modify: `app/core/settings.py`

- [ ] **Step 1: Adicionar variáveis SMTP e CRON_SECRET**

```python
# Adicionar à classe Settings:

CRON_SECRET: str | None = None

SMTP_HOST: str | None = None
SMTP_PORT: int = 587
SMTP_USER: str | None = None
SMTP_PASSWORD: str | None = None
SMTP_USE_TLS: bool = True
NOTIFICATION_EMAIL: str | None = None
NOTIFICATION_FROM: str | None = None
```

- [ ] **Step 2: Verificar inicialização**

```bash
uv run python -c "from app.core.settings import settings; print(settings.SMTP_PORT)"
```

Esperado: `587`

- [ ] **Step 3: Commit**

```bash
git add app/core/settings.py
git commit -m "feat(cron): adicionar CRON_SECRET e SMTP ao settings"
```

---

### Task 2: NotificationService

**Files:**
- Create: `app/modules/cron/application/notification_service.py`

- [ ] **Step 1: Criar `__init__.py`s**

```bash
touch app/modules/cron/__init__.py
touch app/modules/cron/application/__init__.py
touch app/modules/cron/application/use_cases/__init__.py
touch app/modules/cron/adapters/__init__.py
touch app/modules/cron/adapters/http/__init__.py
```

- [ ] **Step 2: Escrever `notification_service.py`**

```python
# app/modules/cron/application/notification_service.py
import logging
from dataclasses import dataclass
from datetime import date

from app.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationItem:
    client_name: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


class NotificationService:
    async def send_summary(
        self,
        target_date: date,
        items: list[NotificationItem],
    ) -> None:
        """Envia e-mail de resumo. Se SMTP não configurado, apenas loga."""
        if not settings.SMTP_HOST:
            logger.warning("SMTP não configurado. Resumo de emissão não enviado.")
            return

        successes = [i for i in items if i.ok]
        errors = [i for i in items if not i.ok]
        subject = (
            f"NFS-e — Resumo de emissão: {target_date} "
            f"({len(successes)} sucesso, {len(errors)} erro)"
        )
        body = self._build_html(target_date, successes, errors)

        try:
            await self._send_email(subject, body)
        except Exception as exc:
            logger.error(f"Falha ao enviar e-mail de resumo: {exc}")

    def _build_html(
        self,
        target_date: date,
        successes: list[NotificationItem],
        errors: list[NotificationItem],
    ) -> str:
        lines = [
            f"<h2>Resumo da emissão do dia {target_date}</h2>",
            f"<p>✅ {len(successes)} nota(s) emitida(s) com sucesso</p>",
            f"<p>❌ {len(errors)} nota(s) com falha</p>",
        ]
        if successes:
            lines.append("<h3>Sucessos</h3><ul>")
            for item in successes:
                pdf_link = (
                    f' <a href="{item.pdf_url}">[PDF]</a>' if item.pdf_url else ""
                )
                lines.append(
                    f"<li>{item.client_name} — NF nº {item.nf_number}{pdf_link}</li>"
                )
            lines.append("</ul>")
        if errors:
            lines.append("<h3>Erros</h3><ul>")
            for item in errors:
                lines.append(f"<li>{item.client_name} — {item.error_message}</li>")
            lines.append("</ul>")
        lines.append(
            "<hr><p><small>Emissão realizada automaticamente pelo sistema Brand Open NFS-e.</small></p>"
        )
        return "".join(lines)

    async def _send_email(self, subject: str, body: str) -> None:
        import aiosmtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.NOTIFICATION_FROM or settings.SMTP_USER or ""
        msg["To"] = settings.NOTIFICATION_EMAIL or ""
        msg.set_content(body, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
        )
```

- [ ] **Step 3: Commit**

```bash
git add app/modules/cron/application/notification_service.py app/modules/cron/ 
git commit -m "feat(cron): NotificationService"
```

---

### Task 3: CronRunner use case

**Files:**
- Create: `app/modules/cron/application/use_cases/cron_runner.py`

- [ ] **Step 1: Escrever `cron_runner.py`**

```python
# app/modules/cron/application/use_cases/cron_runner.py
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from app.core.db.session import db
from app.core.settings import settings
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.poller import DpsPoller
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.cron.application.notification_service import (
    NotificationItem,
    NotificationService,
)
from app.modules.invoices.adapters.db.factories import (
    make_unit_of_work as make_invoices_uow,
)
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork
from app.modules.invoices.application.dtos.commands import (
    CreateInvoiceCommand,
    UpdateInvoiceCommand,
)
from app.modules.recurrences.adapters.db.factories import (
    make_unit_of_work as make_recurrences_uow,
)
from app.modules.recurrences.domain.entities import Recurrence
from app.modules.recurrences.domain.rules import is_due_on

logger = logging.getLogger(__name__)


@dataclass
class CronItemResult:
    recurrence_id: str
    client_name: str
    invoice_id: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


@dataclass
class CronResult:
    date: date
    total: int
    success: int
    error: int
    results: list[CronItemResult] = field(default_factory=list)


class CronRunner:
    def __init__(
        self,
        poller: DpsPoller | None = None,
        notification_service: NotificationService | None = None,
        recurrences_uow_factory=None,
        invoices_uow_factory=None,
        clients_uow_factory=None,
    ) -> None:
        self._poller = poller or DpsPoller()
        self._notification = notification_service or NotificationService()
        self._recurrences_uow_factory = recurrences_uow_factory or make_recurrences_uow
        self._invoices_uow_factory = invoices_uow_factory or make_invoices_uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def run(self, target_date: date) -> CronResult:
        # 1. Busca recorrências devidas hoje
        recurrences_uow = self._recurrences_uow_factory()
        async with recurrences_uow as ruow:
            all_recurrences_with_names = (
                await ruow.recurrences.get_active_due_in_range(target_date, target_date)
            )

        due = [
            (rec, name)
            for rec, name in all_recurrences_with_names
            if is_due_on(rec, target_date)
        ]

        results: list[CronItemResult] = []
        notification_items: list[NotificationItem] = []

        for recurrence, client_name in due:
            item = await self._process_one(recurrence, client_name, target_date)
            results.append(item)
            notification_items.append(
                NotificationItem(
                    client_name=client_name,
                    ok=item.ok,
                    nf_number=item.nf_number,
                    pdf_url=item.pdf_url,
                    error_message=item.error_message,
                )
            )

        await self._notification.send_summary(target_date, notification_items)

        successes = sum(1 for r in results if r.ok)
        return CronResult(
            date=target_date,
            total=len(results),
            success=successes,
            error=len(results) - successes,
            results=results,
        )

    async def _process_one(
        self,
        recurrence: Recurrence,
        client_name: str,
        target_date: date,
    ) -> CronItemResult:
        invoices_uow = self._invoices_uow_factory()

        try:
            # 2a. Idempotência: verificar se já existe sucesso hoje
            async with invoices_uow as iuow:
                existing = await iuow.invoices.get_by_recurrence_and_date(
                    recurrence.id, target_date
                )

            if existing and existing.status == "success":
                logger.info(
                    f"Invoice {existing.id} já emitido com sucesso. Pulando."
                )
                return CronItemResult(
                    recurrence_id=str(recurrence.id),
                    client_name=client_name,
                    invoice_id=str(existing.id),
                    ok=True,
                    nf_number=existing.nf_number,
                    pdf_url=existing.pdf_url,
                )

            # 2b. Busca ou cria invoice
            async with invoices_uow as iuow:
                if existing:
                    # Reutiliza e redefine para pending
                    await iuow.invoices.update(
                        existing.id,
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
                    invoice_id = existing.id
                else:
                    # Snapshot: busca dados do client
                    clients_uow = self._clients_uow_factory()
                    async with clients_uow as cuow:
                        client = await cuow.clients.get_by_id(recurrence.client_id)

                    inv = await iuow.invoices.create(
                        CreateInvoiceCommand(
                            recurrence_id=recurrence.id,
                            client_id=recurrence.client_id,
                            scheduled_date=target_date,
                            amount=recurrence.amount,
                            description=recurrence.description,
                        )
                    )
                    invoice_id = inv.id

            # 2c. Marcar como processing
            async with invoices_uow as iuow:
                await iuow.invoices.update(
                    invoice_id, UpdateInvoiceCommand(status="processing")
                )

            # 2d. Obter próximo nDPS e emitir
            session = db.create_session()
            async with session as sess:
                n_dps = await next_n_dps(sess, settings.BETHA_SERIE)
                await sess.commit()

            clients_uow = self._clients_uow_factory()
            async with clients_uow as cuow:
                client = await cuow.clients.get_by_id(recurrence.client_id)

            payload = DpsPayload(
                recurrence_id=recurrence.id,
                client=client,
                recurrence=recurrence,
                emission_date=target_date,
                n_dps=n_dps,
            )
            result: EmissionResult = await self._poller.emit_and_poll(payload)

            # 2e. Atualizar invoice com resultado
            now = datetime.now(UTC)
            async with invoices_uow as iuow:
                await iuow.invoices.update(
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

            return CronItemResult(
                recurrence_id=str(recurrence.id),
                client_name=client_name,
                invoice_id=str(invoice_id),
                ok=result.ok,
                nf_number=result.nf_number,
                pdf_url=result.pdf_url,
                error_message=result.error_message,
            )

        except Exception as exc:
            logger.exception(f"Erro ao processar recorrência {recurrence.id}: {exc}")
            return CronItemResult(
                recurrence_id=str(recurrence.id),
                client_name=client_name,
                invoice_id="",
                ok=False,
                error_message=str(exc),
            )
```

- [ ] **Step 2: Commit**

```bash
git add app/modules/cron/application/use_cases/cron_runner.py
git commit -m "feat(cron): CronRunner use case"
```

---

### Task 4: Unit tests — CronRunner e NotificationService

**Files:**
- Create: `tests/unit/modules/cron/test_cron_runner.py`
- Create: `tests/unit/modules/cron/test_notification.py`

- [ ] **Step 1: Escrever `test_cron_runner.py`**

```python
# tests/unit/modules/cron/test_cron_runner.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.betha.models import EmissionResult
from app.modules.cron.application.use_cases.cron_runner import CronRunner
from app.modules.invoices.domain.entities import Invoice
from app.modules.recurrences.domain.entities import Recurrence


def _make_recurrence(
    day_of_month: int = 15, is_active: bool = True
) -> Recurrence:
    now = datetime.now(UTC)
    return Recurrence(
        id=uuid.uuid4(), client_id=uuid.uuid4(), description="Serv",
        amount=Decimal("1000.00"), day_of_month=day_of_month,
        start_date=date(2026, 1, 1), end_date=None, is_active=is_active,
        created_at=now, updated_at=now,
    )


def _make_invoice(status: str) -> Invoice:
    now = datetime.now(UTC)
    return Invoice(
        id=uuid.uuid4(), recurrence_id=uuid.uuid4(), client_id=uuid.uuid4(),
        scheduled_date=date(2026, 6, 15), amount=Decimal("1000.00"),
        description="Serv", status=status, n_dps=1, protocol=None,
        nf_number="NF001" if status == "success" else None,
        pdf_url=None, xml_sent=None, xml_response=None, error_message=None,
        emission_date=now if status == "success" else None,
        created_at=now, updated_at=now,
    )


def _make_mock_ruow(recurrences: list) -> MagicMock:
    repo = MagicMock()
    repo.get_active_due_in_range = AsyncMock(return_value=recurrences)
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.recurrences = repo
    return uow


def _make_mock_iuow(existing_invoice: Invoice | None = None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_recurrence_and_date = AsyncMock(return_value=existing_invoice)
    repo.create = AsyncMock(return_value=_make_invoice("pending"))
    repo.update = AsyncMock(return_value=_make_invoice("success"))
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.invoices = repo
    return uow


async def test_cron_skips_already_successful_invoice():
    rec = _make_recurrence(day_of_month=15)
    existing = _make_invoice("success")

    runner = CronRunner(
        poller=MagicMock(),
        notification_service=MagicMock(send_summary=AsyncMock()),
        recurrences_uow_factory=lambda: _make_mock_ruow([(rec, "Cliente A")]),
        invoices_uow_factory=lambda: _make_mock_iuow(existing_invoice=existing),
        clients_uow_factory=lambda: MagicMock(
            __aenter__=AsyncMock(return_value=MagicMock(clients=MagicMock())),
            __aexit__=AsyncMock(),
        ),
    )

    with patch("app.modules.cron.application.use_cases.cron_runner.next_n_dps"):
        with patch("app.modules.cron.application.use_cases.cron_runner.db"):
            result = await runner.run(date(2026, 6, 15))

    assert result.total == 1
    assert result.success == 1
    assert result.results[0].ok is True


async def test_cron_failure_does_not_interrupt_others():
    rec1 = _make_recurrence(day_of_month=15)
    rec2 = _make_recurrence(day_of_month=15)

    call_count = 0

    async def mock_iuow_factory():
        nonlocal call_count
        call_count += 1
        return _make_mock_iuow(existing_invoice=None)

    mock_poller = MagicMock()
    mock_poller.emit_and_poll = AsyncMock(
        side_effect=[
            Exception("Erro grave"),
            EmissionResult(ok=True, nf_number="NF002"),
        ]
    )

    runner = CronRunner(
        poller=mock_poller,
        notification_service=MagicMock(send_summary=AsyncMock()),
        recurrences_uow_factory=lambda: _make_mock_ruow(
            [(rec1, "Cliente A"), (rec2, "Cliente B")]
        ),
        invoices_uow_factory=lambda: _make_mock_iuow(),
        clients_uow_factory=lambda: MagicMock(
            __aenter__=AsyncMock(
                return_value=MagicMock(
                    clients=MagicMock(get_by_id=AsyncMock(return_value=MagicMock()))
                )
            ),
            __aexit__=AsyncMock(),
        ),
    )

    with patch("app.modules.cron.application.use_cases.cron_runner.next_n_dps", new=AsyncMock(return_value=1)):
        with patch("app.modules.cron.application.use_cases.cron_runner.db"):
            result = await runner.run(date(2026, 6, 15))

    assert result.total == 2
```

- [ ] **Step 2: Escrever `test_notification.py`**

```python
# tests/unit/modules/cron/test_notification.py
from datetime import date
from unittest.mock import AsyncMock, patch

from app.modules.cron.application.notification_service import (
    NotificationItem,
    NotificationService,
)


async def test_send_summary_no_smtp_logs_warning():
    service = NotificationService()
    with patch("app.modules.cron.application.notification_service.settings") as s:
        s.SMTP_HOST = None
        items = [NotificationItem(client_name="A", ok=True, nf_number="001")]
        # Deve completar sem erro
        await service.send_summary(date(2026, 6, 15), items)


async def test_build_html_contains_success_and_error():
    service = NotificationService()
    items_ok = [NotificationItem(client_name="A", ok=True, nf_number="NF001", pdf_url="http://pdf")]
    items_err = [NotificationItem(client_name="B", ok=False, error_message="Timeout")]
    html = service._build_html(date(2026, 6, 15), items_ok, items_err)
    assert "NF001" in html
    assert "Timeout" in html
    assert "✅" in html
    assert "❌" in html
```

- [ ] **Step 3: Criar `__init__.py`s de testes**

```bash
touch tests/unit/modules/cron/__init__.py tests/integration/modules/cron/__init__.py
```

- [ ] **Step 4: Rodar unit tests**

```bash
uv run pytest tests/unit/modules/cron/ -v
```

Esperado: todos passam.

- [ ] **Step 5: Commit**

```bash
git add tests/unit/modules/cron/
git commit -m "test(cron): unit tests CronRunner e NotificationService"
```

---

### Task 5: HTTP adapter — schemas, dependencies e router

**Files:**
- Create: `app/modules/cron/adapters/http/schemas.py`
- Create: `app/modules/cron/adapters/http/dependencies.py`
- Create: `app/modules/cron/adapters/http/router.py`

- [ ] **Step 1: Escrever `adapters/http/schemas.py`**

```python
# app/modules/cron/adapters/http/schemas.py
from datetime import date

from pydantic import BaseModel


class CronItemResultSchema(BaseModel):
    recurrence_id: str
    client_name: str
    invoice_id: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


class CronResultSchema(BaseModel):
    date: date
    total: int
    success: int
    error: int
    results: list[CronItemResultSchema]
```

- [ ] **Step 2: Escrever `adapters/http/dependencies.py`**

```python
# app/modules/cron/adapters/http/dependencies.py
from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import decode_access_token
from app.core.settings import settings

bearer = HTTPBearer(auto_error=False)


async def validate_cron_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
) -> None:
    """Aceita Bearer JWT (sessão normal) ou X-Cron-Secret (cron externo)."""
    if credentials:
        try:
            decode_access_token(credentials.credentials)
            return
        except Exception:
            pass

    secret = request.headers.get("X-Cron-Secret")
    if secret and settings.CRON_SECRET and secret == settings.CRON_SECRET:
        return

    raise UnauthorizedError("Autenticação inválida para o endpoint de cron.")
```

- [ ] **Step 3: Escrever `adapters/http/router.py`**

```python
# app/modules/cron/adapters/http/router.py
from datetime import date

from fastapi import APIRouter, Depends

from app.modules.cron.adapters.http.dependencies import validate_cron_auth
from app.modules.cron.adapters.http.schemas import CronResultSchema
from app.modules.cron.application.use_cases.cron_runner import CronItemResult, CronRunner

router = APIRouter(dependencies=[Depends(validate_cron_auth)])


@router.post("/run", response_model=CronResultSchema)
async def run_cron() -> CronResultSchema:
    runner = CronRunner()
    result = await runner.run(date.today())
    return CronResultSchema(
        date=result.date,
        total=result.total,
        success=result.success,
        error=result.error,
        results=[
            {
                "recurrence_id": r.recurrence_id,
                "client_name": r.client_name,
                "invoice_id": r.invoice_id,
                "ok": r.ok,
                "nf_number": r.nf_number,
                "pdf_url": r.pdf_url,
                "error_message": r.error_message,
            }
            for r in result.results
        ],
    )
```

- [ ] **Step 4: Commit**

```bash
git add app/modules/cron/adapters/
git commit -m "feat(cron): HTTP router, schemas e validate_cron_auth"
```

---

### Task 6: Registrar router no app principal

**Files:**
- Modify: `app/api/router.py`

- [ ] **Step 1: Atualizar `app/api/router.py`**

```python
from app.modules.cron.adapters.http.router import router as cron_router
# e dentro de build_api_router():
router.include_router(cron_router, prefix="/cron", tags=["Cron"])
```

- [ ] **Step 2: Commit**

```bash
git add app/api/router.py
git commit -m "feat(cron): registrar router do cron"
```

---

### Task 7: Docker Compose — serviço cron

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Verificar a estrutura atual do `docker-compose.yml`**

```bash
cat docker-compose.yml
```

- [ ] **Step 2: Adicionar serviço `cron`**

Adicionar ao final do arquivo `docker-compose.yml`, dentro de `services:`:

```yaml
  cron:
    image: alpine:3.19
    environment:
      - CRON_SECRET=${CRON_SECRET}
      - API_URL=http://api:8000
    command: >
      sh -c "echo '0 8 * * * wget -qO- --header=\"X-Cron-Secret: $$CRON_SECRET\"
      --post-data=\"\" $$API_URL/cron/run' | crontab - && crond -f -l 2"
    depends_on:
      - api
    restart: unless-stopped
```

Também adicionar `CRON_SECRET` ao `.env.example` se existir.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat(cron): serviço cron no Docker Compose"
```

---

### Task 8: Integration tests

**Files:**
- Create: `tests/integration/modules/cron/conftest.py`
- Create: `tests/integration/modules/cron/test_cron.py`

- [ ] **Step 1: Escrever `conftest.py`**

```python
# tests/integration/modules/cron/conftest.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel


async def insert_client_and_recurrence(
    conn: AsyncConnection,
    *,
    document: str = "10000000001",
    day_of_month: int = 15,
) -> tuple[uuid.UUID, uuid.UUID]:
    client_id = uuid.uuid7()
    rec_id = uuid.uuid7()
    now = datetime.now(tz=UTC)

    await conn.execute(
        insert(ClientModel).values(
            id=client_id, document=document, name=f"Cliente {document}",
            municipal_registration=None, phone=None, email=None,
            zip_code=None, street=None, number=None, complement=None,
            neighborhood=None, ibge_city_code=None, is_active=True,
            created_at=now, updated_at=now,
        )
    )
    await conn.execute(
        insert(RecurrenceModel).values(
            id=rec_id, client_id=client_id, description="Serviço teste",
            amount=Decimal("500.00"), day_of_month=day_of_month,
            start_date=date(2026, 1, 1), end_date=None, is_active=True,
            created_at=now, updated_at=now,
        )
    )
    return client_id, rec_id
```

- [ ] **Step 2: Atualizar `tests/integration/conftest.py`**

Verificar que os UoWs de clients, recurrences e invoices já estão sobrescritos. Não precisa adicionar override para cron (não tem UoW próprio).

- [ ] **Step 3: Escrever `test_cron.py`**

```python
# tests/integration/modules/cron/test_cron.py
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.integrations.betha.models import EmissionResult
from app.core.settings import settings


async def test_cron_auth_jwt_valid(
    client: AsyncClient, auth_headers: dict
) -> None:
    mock_result = MagicMock()
    mock_result.date = date.today()
    mock_result.total = 0
    mock_result.success = 0
    mock_result.error = 0
    mock_result.results = []

    with patch(
        "app.modules.cron.adapters.http.router.CronRunner"
    ) as MockRunner:
        MockRunner.return_value.run = AsyncMock(return_value=mock_result)
        resp = await client.post("/cron/run", headers=auth_headers)

    assert resp.status_code == 200


async def test_cron_auth_cron_secret(client: AsyncClient) -> None:
    mock_result = MagicMock()
    mock_result.date = date.today()
    mock_result.total = 0
    mock_result.success = 0
    mock_result.error = 0
    mock_result.results = []

    with patch("app.modules.cron.adapters.http.dependencies.settings") as mock_settings:
        mock_settings.CRON_SECRET = "supersecret"
        with patch(
            "app.modules.cron.adapters.http.router.CronRunner"
        ) as MockRunner:
            MockRunner.return_value.run = AsyncMock(return_value=mock_result)
            resp = await client.post(
                "/cron/run",
                headers={"X-Cron-Secret": "supersecret"},
            )

    assert resp.status_code == 200


async def test_cron_auth_no_auth_returns_401(client: AsyncClient) -> None:
    resp = await client.post("/cron/run")
    assert resp.status_code == 401


async def test_cron_auth_wrong_secret_returns_401(client: AsyncClient) -> None:
    with patch("app.modules.cron.adapters.http.dependencies.settings") as mock_settings:
        mock_settings.CRON_SECRET = "supersecret"
        resp = await client.post(
            "/cron/run",
            headers={"X-Cron-Secret": "senhaerrada"},
        )
    assert resp.status_code == 401


async def test_cron_idempotency(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    """Rodar POST /cron/run duas vezes não duplica emissão bem-sucedida."""
    today = date.today()
    mock_emission = EmissionResult(
        ok=True, protocol="P1", nf_number="NF001", pdf_url="http://pdf"
    )
    mock_poller = MagicMock()
    mock_poller.emit_and_poll = AsyncMock(return_value=mock_emission)

    from tests.integration.modules.cron.conftest import insert_client_and_recurrence
    client_id, rec_id = await insert_client_and_recurrence(
        db_connection,
        document="20000000001",
        day_of_month=today.day,
    )

    with patch(
        "app.modules.cron.application.use_cases.cron_runner.DpsPoller",
        return_value=mock_poller,
    ):
        with patch(
            "app.modules.cron.application.use_cases.cron_runner.next_n_dps",
            new=AsyncMock(return_value=1),
        ):
            resp1 = await client.post("/cron/run", headers=auth_headers)
            resp2 = await client.post("/cron/run", headers=auth_headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    data2 = resp2.json()
    # No segundo run, a recorrência já foi emitida com sucesso → deve ser pulada
    # O poller não deve ter sido chamado de novo
    assert mock_poller.emit_and_poll.call_count == 1
```

- [ ] **Step 4: Rodar**

```bash
uv run pytest tests/integration/modules/cron/ -v
```

Esperado: todos passam.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/modules/cron/
git commit -m "test(cron): integration tests autenticação e idempotência"
```

---

### Task 9: Instalar dependência aiosmtplib

- [ ] **Step 1: Adicionar dependência**

```bash
uv add aiosmtplib
```

- [ ] **Step 2: Confirmar que `uv.lock` foi atualizado**

```bash
git add uv.lock pyproject.toml
git commit -m "deps: adicionar aiosmtplib para envio de e-mail"
```

---

## Verificação final

- [ ] Lint: `uv run ruff check app/modules/cron/`
- [ ] Type check: `uv run mypy app/modules/cron/`
- [ ] Todos os testes: `uv run pytest tests/ -v`
- [ ] Verificar que a API sobe: `uv run uvicorn app.main:app --reload` (deve inicializar sem erros)

# tests/unit/modules/cron/test_cron_runner.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.integrations.betha.models import EmissionResult
from app.modules.cron.application.use_cases.cron_runner import CronRunner
from app.modules.invoices.domain.entities import Invoice
from app.modules.recurrences.domain.entities import Recurrence


def _make_recurrence(day_of_month: int = 15, is_active: bool = True) -> Recurrence:
    now = datetime.now(UTC)
    return Recurrence(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        description="Serv",
        amount=Decimal("1000.00"),
        day_of_month=day_of_month,
        start_date=date(2026, 1, 1),
        end_date=None,
        is_active=is_active,
        inf_dps={},
        created_at=now,
        updated_at=now,
    )


def _make_invoice(status: str) -> Invoice:
    now = datetime.now(UTC)
    return Invoice(
        id=uuid.uuid4(),
        recurrence_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        scheduled_date=date(2026, 6, 15),
        amount=Decimal("1000.00"),
        description="Serv",
        status=status,
        n_dps=1,
        protocol=None,
        nf_number="NF001" if status == "success" else None,
        pdf_url=None,
        xml_sent=None,
        xml_response=None,
        error_message=None,
        emission_date=now if status == "success" else None,
        created_at=now,
        updated_at=now,
    )


def _make_mock_ruow(recurrences: list) -> MagicMock:
    """Cria mock de unit of work para recorrências retornando list[Recurrence]."""
    repo = MagicMock()
    repo.get_active_due_in_range = AsyncMock(return_value=recurrences)
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.recurrences = repo
    return uow


def _make_mock_iuow(existing_invoice: Invoice | None = None) -> MagicMock:
    """Cria mock de unit of work para invoices."""
    repo = MagicMock()
    repo.get_by_recurrence_and_date = AsyncMock(return_value=existing_invoice)
    repo.create = AsyncMock(return_value=_make_invoice("pending"))
    repo.update = AsyncMock(return_value=_make_invoice("success"))
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.invoices = repo
    return uow


def _make_mock_cuow(client_name: str = "Cliente A") -> MagicMock:
    """Cria mock de unit of work para clientes."""
    mock_client = MagicMock()
    mock_client.name = client_name
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=mock_client)
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.clients = repo
    return uow


async def test_cron_skips_already_successful_invoice():
    rec = _make_recurrence(day_of_month=15)
    existing = _make_invoice("success")

    runner = CronRunner(
        poller=MagicMock(),
        notification_service=MagicMock(send_summary=AsyncMock()),
        # get_active_due_in_range retorna list[Recurrence] (sem nome do cliente)
        recurrences_uow_factory=lambda: _make_mock_ruow([rec]),
        invoices_uow_factory=lambda: _make_mock_iuow(existing_invoice=existing),
        clients_uow_factory=lambda: _make_mock_cuow("Cliente A"),
    )

    with patch("app.modules.cron.application.use_cases.cron_runner.next_n_dps"):
        with patch("app.modules.cron.application.use_cases.cron_runner.db"):
            result = await runner.run(date(2026, 6, 15))

    assert result.total == 1
    assert result.success == 1
    assert result.results[0].ok is True


async def test_cron_failure_does_not_interrupt_others():
    """Falha em uma recorrência não impede processamento das demais."""
    rec1 = _make_recurrence(day_of_month=15)
    rec2 = _make_recurrence(day_of_month=15)

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
        # Retorna duas recorrências sem tupla com nome
        recurrences_uow_factory=lambda: _make_mock_ruow([rec1, rec2]),
        invoices_uow_factory=lambda: _make_mock_iuow(),
        clients_uow_factory=lambda: _make_mock_cuow("Cliente"),
    )

    with patch(
        "app.modules.cron.application.use_cases.cron_runner.next_n_dps",
        new=AsyncMock(return_value=1),
    ):
        with patch("app.modules.cron.application.use_cases.cron_runner.db"):
            result = await runner.run(date(2026, 6, 15))

    assert result.total == 2

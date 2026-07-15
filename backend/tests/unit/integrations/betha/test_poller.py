# tests/unit/integrations/betha/test_poller.py
import ssl
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import DpsPayload, PollResult
from app.integrations.betha.poller import DpsPoller, _make_http_client
from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


def _make_payload() -> DpsPayload:
    now = datetime.now(UTC)
    client = Client(
        id=uuid.uuid4(),
        document="12345678901",
        name="X",
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
        created_at=now,
        updated_at=now,
    )
    recurrence = Recurrence(
        id=uuid.uuid4(),
        client_id=client.id,
        description="Serv",
        amount=Decimal("100.00"),
        day_of_month=15,
        start_date=date(2026, 1, 1),
        end_date=None,
        is_active=True,
        inf_dps={
            "toma": {"CNPJ": "12345678000199", "xNome": "X"},
            "serv": {"cServ": {"xDescServ": "Serv"}},
            "valores": {"vServPrest": {"vServ": "100.00"}},
        },
        created_at=now,
        updated_at=now,
    )
    return DpsPayload(
        recurrence_id=recurrence.id,
        client=client,
        recurrence=recurrence,
        emission_date=date(2026, 6, 15),
        n_dps=1,
    )


async def test_poller_returns_success_on_processado():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT123")
    mock_client.check_status = AsyncMock(
        return_value=PollResult(
            status="PROCESSADO", nf_number="NF001", pdf_url="http://pdf.url"
        )
    )

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is True
    assert result.nf_number == "NF001"
    assert result.protocol == "PROT123"


async def test_poller_returns_error_on_erro_status():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT999")
    mock_client.check_status = AsyncMock(
        return_value=PollResult(status="ERRO", error_message="Documento inválido")
    )

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Documento inválido" in (result.error_message or "")


async def test_poller_timeout_after_max_attempts():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(return_value="PROT777")
    mock_client.check_status = AsyncMock(return_value=PollResult(status="AGUARDANDO"))

    with (
        patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()),
        patch("app.integrations.betha.poller.settings") as mock_settings,
    ):
        mock_settings.BETHA_POLL_MAX_ATTEMPTS = 3
        mock_settings.BETHA_POLL_INTERVAL_S = 0
        mock_settings.BETHA_CERT_PATH = None
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Timeout" in (result.error_message or "")


async def test_poller_submit_error_returns_emission_result_false():
    mock_client = MagicMock()
    mock_client.submit_dps = AsyncMock(side_effect=BethaError("Falha SOAP"))

    with patch("app.integrations.betha.poller.asyncio.sleep", new=AsyncMock()):
        poller = DpsPoller(client=mock_client)
        result = await poller.emit_and_poll(_make_payload())

    assert result.ok is False
    assert "Falha SOAP" in (result.error_message or "")


def test_make_http_client_sem_cert_retorna_cliente_simples():
    with patch("app.integrations.betha.poller.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = None
        client = _make_http_client()

    assert isinstance(client, httpx.AsyncClient)


def test_make_http_client_com_cert_cria_ssl_context(test_cert):
    pfx_path, _ = test_cert

    with (
        patch("app.integrations.betha.poller.settings") as mock_settings,
        patch("app.integrations.betha.poller.httpx.AsyncClient") as mock_async_client,
    ):
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        _make_http_client()

    call_kwargs = mock_async_client.call_args.kwargs
    assert "verify" in call_kwargs
    assert isinstance(call_kwargs["verify"], ssl.SSLContext)

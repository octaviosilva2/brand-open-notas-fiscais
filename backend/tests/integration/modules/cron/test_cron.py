# tests/integration/modules/cron/test_cron.py
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.integrations.betha.models import EmissionResult


async def test_cron_auth_jwt_valid(client: AsyncClient, auth_headers: dict) -> None:
    """Requisição com JWT válido deve ser aceita."""
    mock_result = MagicMock()
    mock_result.date = date.today()
    mock_result.total = 0
    mock_result.success = 0
    mock_result.error = 0
    mock_result.results = []

    with patch("app.modules.cron.adapters.http.router.CronRunner") as MockRunner:
        MockRunner.return_value.run = AsyncMock(return_value=mock_result)
        resp = await client.post("/cron/run", headers=auth_headers)

    assert resp.status_code == 200


async def test_cron_auth_cron_secret(client: AsyncClient) -> None:
    """Requisição com X-Cron-Secret correto deve ser aceita."""
    mock_result = MagicMock()
    mock_result.date = date.today()
    mock_result.total = 0
    mock_result.success = 0
    mock_result.error = 0
    mock_result.results = []

    with patch("app.modules.cron.adapters.http.dependencies.settings") as mock_settings:
        mock_settings.CRON_SECRET = "supersecret"
        with patch("app.modules.cron.adapters.http.router.CronRunner") as MockRunner:
            MockRunner.return_value.run = AsyncMock(return_value=mock_result)
            resp = await client.post(
                "/cron/run",
                headers={"X-Cron-Secret": "supersecret"},
            )

    assert resp.status_code == 200


async def test_cron_auth_no_auth_returns_401(client: AsyncClient) -> None:
    """Requisição sem autenticação deve retornar 401."""
    resp = await client.post("/cron/run")
    assert resp.status_code == 401


async def test_cron_auth_wrong_secret_returns_401(client: AsyncClient) -> None:
    """Requisição com secret errado deve retornar 401."""
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
    assert mock_poller.emit_and_poll.call_count == 1

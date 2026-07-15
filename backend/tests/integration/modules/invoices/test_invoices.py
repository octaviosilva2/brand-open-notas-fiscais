# tests/integration/modules/invoices/test_invoices.py
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.integrations.betha.models import EmissionResult


async def test_list_invoices(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """Listagem básica de invoices deve retornar ao menos 1 item."""
    resp = await client.get("/invoices", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert data["total"] >= 1


async def test_list_invoices_filter_status(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """Filtrar por status deve retornar apenas invoices com aquele status."""
    resp = await client.get("/invoices?status=success", headers=auth_headers)
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["status"] == "success"


async def test_list_invoices_filter_client(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """Filtrar por client_id deve retornar invoices daquele cliente."""
    cid = test_ids["client_id"]
    resp = await client.get(f"/invoices?client_id={cid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_get_invoice(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """GET de invoice existente deve retornar os detalhes com xml_sent."""
    iid = test_ids["invoice_id"]
    resp = await client.get(f"/invoices/{iid}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(iid)
    assert "xml_sent" in data


async def test_get_invoice_not_found(client: AsyncClient, auth_headers: dict) -> None:
    """GET de invoice inexistente deve retornar 404."""
    resp = await client.get(f"/invoices/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_download_xml(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """Download do XML deve retornar content-type application/xml com o conteúdo correto."""
    iid = test_ids["invoice_id"]
    resp = await client.get(f"/invoices/{iid}/xml", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/xml")
    assert "<xml>" in resp.text


async def test_download_xml_not_available(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    """Download do XML de invoice sem xml_sent deve retornar 404."""
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )

    cid = await _insert_client(db_connection, document="88888888801")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(db_connection, rid, cid, xml_sent=None, nf_number=None)
    resp = await client.get(f"/invoices/{iid}/xml", headers=auth_headers)
    assert resp.status_code == 404


async def test_pdf_redirect(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """GET de PDF deve redirecionar (302) para a URL do PDF."""
    iid = test_ids["invoice_id"]
    resp = await client.get(
        f"/invoices/{iid}/pdf", headers=auth_headers, follow_redirects=False
    )
    assert resp.status_code == 302
    assert "pdf.example.com" in resp.headers["location"]


async def test_pdf_not_available(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    """GET de PDF de invoice sem pdf_url deve retornar 404."""
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )

    cid = await _insert_client(db_connection, document="77777777701")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(db_connection, rid, cid, pdf_url=None, nf_number=None)
    resp = await client.get(
        f"/invoices/{iid}/pdf", headers=auth_headers, follow_redirects=False
    )
    assert resp.status_code == 404


async def test_retry_success_invoice_returns_409(
    client: AsyncClient, auth_headers: dict, test_ids: dict
) -> None:
    """Retry em invoice com status 'success' deve retornar 409 Conflict."""
    iid = test_ids["invoice_id"]
    resp = await client.post(f"/invoices/{iid}/retry", headers=auth_headers)
    assert resp.status_code == 409


async def test_retry_error_invoice(
    client: AsyncClient, auth_headers: dict, db_connection
) -> None:
    """Retry em invoice com status 'error' deve emitir via Betha e retornar 200."""
    from tests.integration.modules.invoices.conftest import (
        _insert_client,
        _insert_recurrence,
        insert_invoice,
    )

    cid = await _insert_client(db_connection, document="66666666601")
    rid = await _insert_recurrence(db_connection, cid)
    iid = await insert_invoice(
        db_connection, rid, cid, status="error", nf_number=None, xml_sent="<xml/>"
    )

    # Mock do resultado da emissão Betha
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

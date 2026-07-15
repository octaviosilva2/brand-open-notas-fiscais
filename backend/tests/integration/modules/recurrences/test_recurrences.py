# tests/integration/modules/recurrences/test_recurrences.py
import uuid
from datetime import date

from httpx import AsyncClient

_INF_DPS = {
    "toma": {
        "CNPJ": "12345678000199",
        "xNome": "Cliente X",
        "email": None,
    },
    "serv": {"cServ": {"xDescServ": "Consultoria", "cTribNac": None}},
    "valores": {"vServPrest": {"vServ": "1500.00"}},
}


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
            "inf_dps": _INF_DPS,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["client_id"] == str(test_client_id)
    assert data["day_of_month"] == 15
    # inf_dps volta sem as chaves None
    assert data["inf_dps"]["toma"]["CNPJ"] == "12345678000199"
    assert "email" not in data["inf_dps"]["toma"]
    assert "cTribNac" not in data["inf_dps"]["serv"]["cServ"]


async def test_create_recurrence_requires_inf_dps(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.post(
        "/recurrences",
        json={
            "client_id": str(test_client_id),
            "description": "Sem inf_dps",
            "amount": "100.00",
            "day_of_month": 1,
            "start_date": "2026-01-01",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_update_recurrence_inf_dps_parcial(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    create = await client.post(
        "/recurrences",
        json={
            "client_id": str(test_client_id),
            "description": "Para atualizar",
            "amount": "1500.00",
            "day_of_month": 10,
            "start_date": "2026-01-01",
            "inf_dps": _INF_DPS,
        },
        headers=auth_headers,
    )
    assert create.status_code == 201
    rec_id = create.json()["id"]

    resp = await client.patch(
        f"/recurrences/{rec_id}",
        json={
            "inf_dps": {
                "serv": {"cServ": {"xDescServ": "Novo serviço"}},
                "valores": {"vServPrest": {"vServ": "2000.00"}},
            }
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    inf = resp.json()["inf_dps"]
    assert inf["serv"]["cServ"]["xDescServ"] == "Novo serviço"
    assert inf["valores"]["vServPrest"]["vServ"] == "2000.00"


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
            "inf_dps": _INF_DPS,
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
    ids = [i["id"] for i in resp.json()["data"]]
    assert str(test_recurrence_id) in ids


async def test_list_recurrences_filter_client(
    client: AsyncClient,
    auth_headers: dict,
    test_client_id: uuid.UUID,
    test_recurrence_id: uuid.UUID,
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
    resp = await client.delete(
        f"/recurrences/{test_recurrence_id}", headers=auth_headers
    )
    assert resp.status_code == 405


async def test_delete_client_with_recurrence_returns_409(
    client: AsyncClient,
    auth_headers: dict,
    test_client_id: uuid.UUID,
    test_recurrence_id: uuid.UUID,
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

    await insert_recurrence(
        db_connection, test_client_id, day_of_month=15, end_date=date(2026, 5, 31)
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

# tests/integration/modules/clients/test_clients.py
import uuid

from httpx import AsyncClient


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


async def test_get_client_not_found(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.get(f"/clients/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_list_clients(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert data["total"] >= 1


async def test_search_clients_by_name(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients?search=Cliente", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert any(i["id"] == str(test_client_id) for i in items)


async def test_search_clients_by_document(
    client: AsyncClient, auth_headers: dict, test_client_id: uuid.UUID
) -> None:
    resp = await client.get("/clients?search=12345678901", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["data"]
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

    await insert_client(db_connection, document="11111111111", name="A")
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

    uid = await insert_client(
        db_connection, document="99999999901", name="Para Deletar"
    )
    resp = await client.delete(f"/clients/{uid}", headers=auth_headers)
    assert resp.status_code == 204


async def test_delete_client_not_found(client: AsyncClient, auth_headers: dict) -> None:
    resp = await client.delete(f"/clients/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get("/clients")
    assert resp.status_code == 401

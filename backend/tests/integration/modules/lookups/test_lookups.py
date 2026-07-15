# tests/integration/modules/lookups/test_lookups.py
from httpx import AsyncClient


async def test_lookup_municipios_requer_auth(client: AsyncClient) -> None:
    resp = await client.get("/lookups/municipios")
    assert resp.status_code == 401


async def test_lookup_municipios_filtra(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get(
        "/lookups/municipios", params={"q": "jara"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert any(o["value"] == "4208906" for o in resp.json())


async def test_lookup_paises_sem_query_respeita_limit(
    client: AsyncClient, auth_headers: dict
) -> None:
    resp = await client.get(
        "/lookups/paises", params={"limit": 2}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) <= 2

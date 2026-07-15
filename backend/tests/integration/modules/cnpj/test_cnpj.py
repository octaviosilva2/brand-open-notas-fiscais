from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from httpx import AsyncClient

_CNPJ_VALIDO = "12345678000195"
_CNPJ_URL = f"/api/cnpj/{_CNPJ_VALIDO}"
_BASE_BRASILAPI = "https://brasilapi.com.br/api/cnpj/v1"


def _make_brasilapi_response(
    *,
    razao_social: str = "Empresa Teste Ltda",
    ibge: Any = 3550308,
) -> dict[str, Any]:
    return {
        "razao_social": razao_social,
        "ddd_telefone_1": "11999990001",
        "email": "contato@empresa.com",
        "cep": "01310100",
        "logradouro": "Av. Paulista",
        "numero": "1000",
        "complemento": "Sala 1",
        "bairro": "Bela Vista",
        "codigo_municipio_ibge": ibge,
    }


def _make_http_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", f"{_BASE_BRASILAPI}/{_CNPJ_VALIDO}")
    return httpx.HTTPStatusError(
        f"HTTP {status_code}", request=request, response=httpx.Response(status_code)
    )


class TestGetCnpjSucesso:
    async def test_200_retorna_name(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.return_value = _make_brasilapi_response()
        resp = await client.get(_CNPJ_URL)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Empresa Teste Ltda"

    async def test_200_retorna_todos_os_campos(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.return_value = _make_brasilapi_response()
        resp = await client.get(_CNPJ_URL)
        data = resp.json()
        assert data["name"] == "Empresa Teste Ltda"
        assert data["phone"] == "11999990001"
        assert data["email"] == "contato@empresa.com"
        assert data["zip_code"] == "01310100"
        assert data["street"] == "Av. Paulista"
        assert data["number"] == "1000"
        assert data["complement"] == "Sala 1"
        assert data["neighborhood"] == "Bela Vista"

    async def test_200_ibge_como_string_no_json(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.return_value = _make_brasilapi_response(
            ibge=4208906
        )
        resp = await client.get(_CNPJ_URL)
        assert resp.json()["ibge_city_code"] == "4208906"


class TestGetCnpjErrosDeCliente:
    async def test_422_cnpj_com_13_digitos(self, client: AsyncClient) -> None:
        resp = await client.get("/api/cnpj/1234567800019")
        assert resp.status_code == 422

    async def test_422_cnpj_com_15_digitos(self, client: AsyncClient) -> None:
        resp = await client.get("/api/cnpj/123456780001950")
        assert resp.status_code == 422

    async def test_422_cnpj_com_apenas_12_digitos(self, client: AsyncClient) -> None:
        resp = await client.get("/api/cnpj/123456780001")
        assert resp.status_code == 422


class TestGetCnpjErrosDeGateway:
    async def test_404_quando_brasilapi_nao_encontra(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.side_effect = _make_http_error(404)
        resp = await client.get(_CNPJ_URL)
        assert resp.status_code == 404

    async def test_502_quando_brasilapi_retorna_500(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.side_effect = _make_http_error(500)
        resp = await client.get(_CNPJ_URL)
        assert resp.status_code == 502

    async def test_502_quando_brasilapi_indisponivel(
        self, client: AsyncClient, brasilapi_mock: AsyncMock
    ) -> None:
        brasilapi_mock.get_cnpj_info.side_effect = httpx.ConnectError("timeout")
        resp = await client.get(_CNPJ_URL)
        assert resp.status_code == 502

    @pytest.mark.parametrize("status_code", [429, 503, 504])
    async def test_5xx_e_outros_erros_retornam_502(
        self, client: AsyncClient, brasilapi_mock: AsyncMock, status_code: int
    ) -> None:
        brasilapi_mock.get_cnpj_info.side_effect = _make_http_error(status_code)
        resp = await client.get(_CNPJ_URL)
        assert resp.status_code == 502

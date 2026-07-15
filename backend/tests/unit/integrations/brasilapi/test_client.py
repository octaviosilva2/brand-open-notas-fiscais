from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.integrations.brasilapi.client import BrasilApiClient

_CNPJ = "12345678000195"
_BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"


def _make_response(status_code: int, body: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body or {}
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=httpx.Request("GET", f"{_BASE_URL}/{_CNPJ}"),
            response=httpx.Response(status_code),
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


@pytest.fixture
def mock_http() -> AsyncMock:
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def client(mock_http: AsyncMock) -> BrasilApiClient:
    return BrasilApiClient(http=mock_http)


class TestCnpjValido:
    async def test_chama_url_correta(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        mock_http.get.return_value = _make_response(200, {"razao_social": "X"})
        await client.get_cnpj_info(_CNPJ)
        mock_http.get.assert_awaited_once_with(f"{_BASE_URL}/{_CNPJ}")

    async def test_retorna_json_da_resposta(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        body = {"razao_social": "Empresa X", "cep": "01310100"}
        mock_http.get.return_value = _make_response(200, body)
        result = await client.get_cnpj_info(_CNPJ)
        assert result == body

    async def test_chama_raise_for_status(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        resp = _make_response(200)
        mock_http.get.return_value = resp
        await client.get_cnpj_info(_CNPJ)
        resp.raise_for_status.assert_called_once()


class TestCnpjInvalido:
    async def test_int_levanta_value_error(self, client: BrasilApiClient) -> None:
        with pytest.raises(ValueError):
            await client.get_cnpj_info(12345678000195)  # type: ignore[arg-type]

    async def test_menos_de_14_digitos_levanta_value_error(
        self, client: BrasilApiClient
    ) -> None:
        with pytest.raises(ValueError):
            await client.get_cnpj_info("1234567800019")

    async def test_mais_de_14_digitos_levanta_value_error(
        self, client: BrasilApiClient
    ) -> None:
        with pytest.raises(ValueError):
            await client.get_cnpj_info("123456780001950")

    async def test_com_mascara_levanta_value_error(
        self, client: BrasilApiClient
    ) -> None:
        with pytest.raises(ValueError):
            await client.get_cnpj_info("12.345.678/0001-95")

    async def test_mensagem_do_value_error(self, client: BrasilApiClient) -> None:
        with pytest.raises(
            ValueError, match="CNPJ deve ser uma string de 14 dígitos numéricos."
        ):
            await client.get_cnpj_info("invalido")


class TestErrosHttp:
    async def test_404_propaga_http_status_error(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        mock_http.get.return_value = _make_response(404)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_cnpj_info(_CNPJ)

    async def test_500_propaga_http_status_error(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        mock_http.get.return_value = _make_response(500)
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_cnpj_info(_CNPJ)

    async def test_nao_encapsula_excecao_em_tipo_de_dominio(
        self, client: BrasilApiClient, mock_http: AsyncMock
    ) -> None:
        mock_http.get.return_value = _make_response(404)
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await client.get_cnpj_info(_CNPJ)
        assert type(exc_info.value) is httpx.HTTPStatusError

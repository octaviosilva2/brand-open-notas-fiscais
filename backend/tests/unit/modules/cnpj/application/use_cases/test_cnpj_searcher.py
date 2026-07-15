from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from app.core.exceptions import BadGatewayError, NotFoundError, ValidationAppError
from app.modules.cnpj.application.use_cases.cnpj_searcher import CnpjSearcher
from app.modules.cnpj.domain.entities import CnpjInfo

_CNPJ = "12345678000195"


def _make_api_response(
    *,
    razao_social: str | None = "Empresa X",
    ibge: Any = 1234567,
    **overrides: Any,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "razao_social": razao_social,
        "ddd_telefone_1": "11999990000",
        "email": "empresa@x.com",
        "cep": "01310100",
        "logradouro": "Av. Paulista",
        "numero": "1000",
        "complemento": "Sala 1",
        "bairro": "Bela Vista",
        "codigo_municipio_ibge": ibge,
    }
    base.update(overrides)
    return base


def _make_http_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", f"https://brasilapi.com.br/api/cnpj/v1/{_CNPJ}")
    response = httpx.Response(status_code)
    return httpx.HTTPStatusError(
        f"HTTP {status_code}", request=request, response=response
    )


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def searcher(mock_client: AsyncMock) -> CnpjSearcher:
    return CnpjSearcher(client=mock_client)


class TestMapeamentoDeCampos:
    async def test_retorna_instancia_de_cnpj_info(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert isinstance(result, CnpjInfo)

    async def test_razao_social_vai_para_name(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response(
            razao_social="Minha Empresa"
        )
        result = await searcher.search(_CNPJ)
        assert result.name == "Minha Empresa"

    async def test_ddd_telefone_vai_para_phone(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.phone == "11999990000"

    async def test_email_mapeado(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.email == "empresa@x.com"

    async def test_cep_vai_para_zip_code(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.zip_code == "01310100"

    async def test_logradouro_vai_para_street(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.street == "Av. Paulista"

    async def test_numero_vai_para_number(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.number == "1000"

    async def test_complemento_mapeado(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.complement == "Sala 1"

    async def test_bairro_vai_para_neighborhood(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response()
        result = await searcher.search(_CNPJ)
        assert result.neighborhood == "Bela Vista"


class TestIbgeCityCode:
    async def test_ibge_inteiro_convertido_para_string(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response(ibge=4208906)
        result = await searcher.search(_CNPJ)
        assert result.ibge_city_code == "4208906"

    async def test_ibge_none_permanece_none(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response(ibge=None)
        result = await searcher.search(_CNPJ)
        assert result.ibge_city_code is None

    async def test_ibge_ausente_do_dict_retorna_none(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        response = _make_api_response()
        del response["codigo_municipio_ibge"]
        mock_client.get_cnpj_info.return_value = response
        result = await searcher.search(_CNPJ)
        assert result.ibge_city_code is None


class TestErrosHttp:
    async def test_404_levanta_not_found_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = _make_http_error(404)
        with pytest.raises(NotFoundError):
            await searcher.search(_CNPJ)

    async def test_404_mensagem_correta(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = _make_http_error(404)
        with pytest.raises(NotFoundError) as exc_info:
            await searcher.search(_CNPJ)
        assert exc_info.value.message == "CNPJ não encontrado."

    async def test_5xx_levanta_bad_gateway_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = _make_http_error(500)
        with pytest.raises(BadGatewayError):
            await searcher.search(_CNPJ)

    async def test_503_levanta_bad_gateway_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = _make_http_error(503)
        with pytest.raises(BadGatewayError):
            await searcher.search(_CNPJ)

    async def test_request_error_levanta_bad_gateway(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = httpx.ConnectError("timeout")
        with pytest.raises(BadGatewayError):
            await searcher.search(_CNPJ)

    async def test_bad_gateway_mensagem_correta(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.side_effect = _make_http_error(500)
        with pytest.raises(BadGatewayError) as exc_info:
            await searcher.search(_CNPJ)
        assert exc_info.value.message == "Serviço de consulta indisponível."


class TestValidacaoRazaoSocial:
    async def test_razao_social_none_levanta_validation_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response(razao_social=None)
        with pytest.raises(ValidationAppError):
            await searcher.search(_CNPJ)

    async def test_razao_social_vazia_levanta_validation_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        mock_client.get_cnpj_info.return_value = _make_api_response(razao_social="")
        with pytest.raises(ValidationAppError):
            await searcher.search(_CNPJ)

    async def test_chave_razao_social_ausente_levanta_validation_error(
        self, searcher: CnpjSearcher, mock_client: AsyncMock
    ) -> None:
        response = _make_api_response()
        del response["razao_social"]
        mock_client.get_cnpj_info.return_value = response
        with pytest.raises(ValidationAppError):
            await searcher.search(_CNPJ)

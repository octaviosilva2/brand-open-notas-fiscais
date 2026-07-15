from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request
from httpx import AsyncClient

from app.core.exceptions import ValidationAppError
from app.integrations.brasilapi.client import BrasilApiClient
from app.modules.cnpj.adapters.http.depencencies import get_brasilapi_client, get_cnpj


@pytest.fixture
def mock_request() -> MagicMock:
    req = MagicMock(spec=Request)
    req.app.state.brasilapi_client = AsyncMock(spec=AsyncClient)
    return req


class TestGetCnpj:
    def test_cnpj_so_digitos_retorna_mesmo_valor(self) -> None:
        result = get_cnpj("12345678000195")
        assert result == "12345678000195"

    def test_cnpj_com_mascara_remove_nao_digitos(self) -> None:
        result = get_cnpj("12.345.678/0001-95")
        assert result == "12345678000195"

    def test_cnpj_com_pontos_e_barra(self) -> None:
        result = get_cnpj("00.000.000/0001-91")
        assert result == "00000000000191"

    def test_13_digitos_levanta_validation_error(self) -> None:
        with pytest.raises(ValidationAppError):
            get_cnpj("1234567800019")

    def test_15_digitos_levanta_validation_error(self) -> None:
        with pytest.raises(ValidationAppError):
            get_cnpj("123456780001950")

    def test_vazio_levanta_validation_error(self) -> None:
        with pytest.raises(ValidationAppError):
            get_cnpj("")

    def test_retorno_e_string(self) -> None:
        result = get_cnpj("12345678000195")
        assert isinstance(result, str)


class TestGetBrasilApiClient:
    def test_retorna_instancia_de_brasil_api_client(
        self, mock_request: MagicMock
    ) -> None:
        result = get_brasilapi_client(mock_request)
        assert isinstance(result, BrasilApiClient)

    def test_usa_http_client_do_app_state(self, mock_request: MagicMock) -> None:
        result = get_brasilapi_client(mock_request)
        assert result._http is mock_request.app.state.brasilapi_client

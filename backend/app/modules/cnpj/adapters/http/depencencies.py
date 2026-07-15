import re
from typing import Annotated

from fastapi import Depends, Path, Request

from app.core.exceptions import ValidationAppError
from app.integrations.brasilapi.client import BrasilApiClient


def get_brasilapi_client(
    request: Request,
) -> BrasilApiClient:
    """
    Fornece uma instância do cliente HTTP para a BrasilAPI.

    Args:
        request (Request): O objeto de requisição FastAPI.

    Returns:
        BrasilApiClient: Uma instância do cliente HTTP configurada para a BrasilAPI.
    """

    http_client = request.app.state.brasilapi_client
    return BrasilApiClient(
        http=http_client,
    )


def get_cnpj(cnpj: str = Path(...)) -> str:
    digits = re.sub(r"\D", "", cnpj)
    if len(digits) != 14:
        raise ValidationAppError("CNPJ inválido.")
    return digits


BrasilApiClientDep = Annotated[BrasilApiClient, Depends(get_brasilapi_client)]
CnpjDep = Annotated[str, Depends(get_cnpj)]

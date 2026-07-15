from fastapi import APIRouter, Depends

from app.modules.cnpj.adapters.http.depencencies import BrasilApiClientDep, CnpjDep
from app.modules.cnpj.adapters.http.schemas import CnpjInfoResponse
from app.modules.cnpj.application.use_cases.cnpj_searcher import CnpjSearcher
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("/{cnpj}")
async def get_cnpj_info(
    cnpj: CnpjDep,
    http_client: BrasilApiClientDep,
) -> CnpjInfoResponse:
    """Endpoint para consultar informações de um CNPJ utilizando a BrasilAPI."""

    searcher = CnpjSearcher(client=http_client)
    cnpj_info = await searcher.search(cnpj)
    return CnpjInfoResponse.model_validate(cnpj_info.to_dict())

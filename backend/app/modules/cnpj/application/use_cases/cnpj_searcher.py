import httpx

from app.core.exceptions import BadGatewayError, NotFoundError, ValidationAppError
from app.modules.cnpj.application.ports.cnpj_searcher import CnpjSearcherClient
from app.modules.cnpj.domain.entities import CnpjInfo


class CnpjSearcher:
    def __init__(self, client: CnpjSearcherClient) -> None:
        """
        Inicializa o CnpjSearcher.

        Args:
            client (CnpjSearcherClient):
                O cliente responsável por realizar a busca de informações do CNPJ.
        """

        self._searcher = client

    async def search(self, cnpj: str) -> CnpjInfo:
        """
        Realiza a busca de informações do CNPJ e retorna os dados formatados.

        Args:
            cnpj (str):
                O número do CNPJ a ser consultado.
        Returns:
            CnpjInfo:
                Um objeto contendo as informações do CNPJ formatadas.
        """

        try:
            cnpj_info = await self._searcher.get_cnpj_info(cnpj)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise NotFoundError("CNPJ não encontrado.") from exc
            raise BadGatewayError("Serviço de consulta indisponível.") from exc
        except httpx.RequestError as exc:
            raise BadGatewayError("Serviço de consulta indisponível.") from exc

        ibge_raw = cnpj_info.get("codigo_municipio_ibge")
        info = CnpjInfo(
            name=cnpj_info.get("razao_social"),
            phone=cnpj_info.get("ddd_telefone_1"),
            email=cnpj_info.get("email"),
            zip_code=cnpj_info.get("cep"),
            street=cnpj_info.get("logradouro"),
            number=cnpj_info.get("numero"),
            complement=cnpj_info.get("complemento"),
            neighborhood=cnpj_info.get("bairro"),
            ibge_city_code=str(ibge_raw) if ibge_raw is not None else None,
        )
        if not info.name:
            raise ValidationAppError("CNPJ inválido.")
        return info

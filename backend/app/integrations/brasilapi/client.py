from httpx import AsyncClient


class BrasilApiClient:
    def __init__(self, http: AsyncClient) -> None:
        self._http = http

    async def get_cnpj_info(self, cnpj: str) -> dict:
        """
        Consulta informações de um CNPJ na BrasilAPI.

        Args:
            cnpj (str):
                O número do CNPJ a ser consultado, deve conter 14 dígitos numéricos.
        Returns:
            dict: Um dicionário contendo as informações retornadas pela BrasilAPI.
        Raises:
            ValueError: Se o CNPJ fornecido não for uma string de 14 dígitos numéricos.
            httpx.HTTPError: Se ocorrer um erro na requisição HTTP para a BrasilAPI.
        """

        if not isinstance(cnpj, str) or len(cnpj) != 14 or not cnpj.isdigit():
            raise ValueError("CNPJ deve ser uma string de 14 dígitos numéricos.")

        resp = await self._http.get(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}")
        resp.raise_for_status()
        return resp.json()

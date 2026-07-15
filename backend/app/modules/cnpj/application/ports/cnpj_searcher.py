from typing import Any, Protocol

from httpx import AsyncClient


class CnpjSearcherClient(Protocol):
    def __init__(
        self,
        http: AsyncClient,
    ) -> None: ...

    async def get_cnpj_info(self, cnpj: str) -> dict[str, Any]: ...

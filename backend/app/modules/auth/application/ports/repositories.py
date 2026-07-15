import uuid
from typing import Protocol

from app.modules.auth.domain.entities import Credentials


class AuthRepositoryProtocol(Protocol):
    """Contrato do repositório de credenciais consumido pelos use cases de auth."""

    async def get_credentials_by_email(self, email: str) -> Credentials | None: ...

    async def get_credentials_by_id(self, id_: uuid.UUID) -> Credentials | None: ...

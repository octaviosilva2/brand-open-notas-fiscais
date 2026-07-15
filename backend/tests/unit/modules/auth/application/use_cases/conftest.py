import uuid
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.security.passwords import hash_password
from app.modules.auth.domain.entities import Credentials


class FakeAuthUnitOfWork:
    """Fake de `AuthUnitOfWorkProtocol` para testar os use cases isoladamente.

    Expõe `credentials` como um `AsyncMock` (o repositório) e registra se o
    context manager foi corretamente aberto e fechado.
    """

    def __init__(self, credentials: AsyncMock) -> None:
        self.credentials = credentials
        self.entered = False
        self.exited = False
        self.exit_exc_type: type[BaseException] | None = None

    async def __aenter__(self) -> Self:
        self.entered = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.exited = True
        self.exit_exc_type = exc_type
        return None


@pytest.fixture
def credentials_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(credentials_repo: AsyncMock) -> FakeAuthUnitOfWork:
    return FakeAuthUnitOfWork(credentials_repo)


@pytest.fixture
def credentials() -> Credentials:
    return Credentials(
        id=uuid.uuid4(),
        password_hash=hash_password("senha1234"),
        is_active=True,
    )

import uuid
from datetime import datetime
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.modules.users.domain.entities import User


class FakeUsersUnitOfWork:
    """Fake de `UsersUnitOfWorkProtocol` para testar os use cases isoladamente.

    Expõe `users` como um `AsyncMock` (o repositório) e registra se o context
    manager foi corretamente aberto e fechado.
    """

    def __init__(self, users: AsyncMock) -> None:
        self.users = users
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
def users_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(users_repo: AsyncMock) -> FakeUsersUnitOfWork:
    return FakeUsersUnitOfWork(users_repo)


@pytest.fixture
def user() -> User:
    now = datetime(2026, 6, 11, 12, 0, 0)
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        name="Fulano",
        phone="11999999999",
        is_active=True,
        updated_at=now,
        created_at=now,
    )

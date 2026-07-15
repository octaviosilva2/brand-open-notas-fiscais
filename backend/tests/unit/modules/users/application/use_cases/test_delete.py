import uuid
from unittest.mock import AsyncMock

import pytest

from app.modules.users.application.use_cases.delete import UsersDeleter

from .conftest import FakeUsersUnitOfWork


class TestDelete:
    async def test_calls_repository_with_id(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        deleter = UsersDeleter(uow)
        id_ = uuid.uuid4()

        await deleter.delete(id_)

        users_repo.delete.assert_awaited_once_with(id_)

    async def test_returns_none(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        deleter = UsersDeleter(uow)

        result = await deleter.delete(uuid.uuid4())

        assert result is None

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        deleter = UsersDeleter(uow)

        await deleter.delete(uuid.uuid4())

        assert uow.entered
        assert uow.exited

    async def test_propagates_repository_error_and_exits_context(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        users_repo.delete.side_effect = ValueError("não encontrado")
        deleter = UsersDeleter(uow)

        with pytest.raises(ValueError, match="não encontrado"):
            await deleter.delete(uuid.uuid4())

        assert uow.exited
        assert uow.exit_exc_type is ValueError

import uuid
from unittest.mock import AsyncMock

import pytest

from app.modules.users.application.use_cases.read import UsersReader
from app.modules.users.domain.entities import User

from .conftest import FakeUsersUnitOfWork


class TestGetById:
    async def test_returns_user_from_repository(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_id.return_value = user
        reader = UsersReader(uow)

        result = await reader.get_by_id(user.id)

        assert result is user

    async def test_calls_repository_with_id(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_id.return_value = user
        reader = UsersReader(uow)
        id_ = uuid.uuid4()

        await reader.get_by_id(id_)

        users_repo.get_by_id.assert_awaited_once_with(id_)

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_id.return_value = user
        reader = UsersReader(uow)

        await reader.get_by_id(user.id)

        assert uow.entered
        assert uow.exited

    async def test_propagates_repository_error_and_exits_context(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        users_repo.get_by_id.side_effect = ValueError("não encontrado")
        reader = UsersReader(uow)

        with pytest.raises(ValueError, match="não encontrado"):
            await reader.get_by_id(uuid.uuid4())

        assert uow.exited
        assert uow.exit_exc_type is ValueError

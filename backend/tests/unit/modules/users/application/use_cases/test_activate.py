import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.modules.users.application.use_cases.activate import UsersActivator
from app.modules.users.domain.entities import UpdateUser, User

from .conftest import FakeUsersUnitOfWork


@pytest.fixture
def actor() -> UserActor:
    return UserActor(user_id=uuid.uuid4())


class TestActivate:
    async def test_updates_repository_with_is_active_true(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)
        id_ = uuid.uuid4()

        await activator.activate(id_, actor)

        users_repo.update.assert_awaited_once_with(
            id_=id_,
            update_command=UpdateUser(is_active=True),
        )

    async def test_returns_user_from_repository(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)

        result = await activator.activate(uuid.uuid4(), actor)

        assert result is user

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)

        await activator.activate(uuid.uuid4(), actor)

        assert uow.entered
        assert uow.exited


class TestDeactivate:
    async def test_updates_repository_with_is_active_false(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)
        id_ = uuid.uuid4()

        await activator.deactivate(id_, actor)

        users_repo.update.assert_awaited_once_with(
            id_=id_,
            update_command=UpdateUser(is_active=False),
        )

    async def test_returns_user_from_repository(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)

        result = await activator.deactivate(uuid.uuid4(), actor)

        assert result is user

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
        actor: UserActor,
    ):
        users_repo.update.return_value = user
        activator = UsersActivator(uow)

        await activator.deactivate(uuid.uuid4(), actor)

        assert uow.entered
        assert uow.exited


class TestErrorPropagation:
    async def test_propagates_repository_error_and_exits_context(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        actor: UserActor,
    ):
        users_repo.update.side_effect = ValueError("não encontrado")
        activator = UsersActivator(uow)

        with pytest.raises(ValueError, match="não encontrado"):
            await activator.activate(uuid.uuid4(), actor)

        assert uow.exited
        assert uow.exit_exc_type is ValueError

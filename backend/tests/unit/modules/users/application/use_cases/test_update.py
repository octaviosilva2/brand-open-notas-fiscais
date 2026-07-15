import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.security.passwords import verify_password
from app.modules.users.application.dtos.commands import UpdateUserCommand
from app.modules.users.application.use_cases.update import UsersUpdater
from app.modules.users.domain.entities import UpdateUser, User

from .conftest import FakeUsersUnitOfWork


class TestUpdate:
    async def test_maps_defined_fields_to_update_command(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand(email="novo@example.com", name="Novo")

        await updater.update(id_, command)

        users_repo.update.assert_awaited_once_with(
            id_=id_,
            update_command=UpdateUser(email="novo@example.com", name="Novo"),
        )

    async def test_only_defined_fields_are_set(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand(is_active=False)

        await updater.update(id_, command)

        users_repo.update.assert_awaited_once_with(
            id_=id_,
            update_command=UpdateUser(is_active=False),
        )

    async def test_command_with_no_defined_fields_produces_empty_update(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand()

        await updater.update(id_, command)

        users_repo.update.assert_awaited_once_with(
            id_=id_,
            update_command=UpdateUser(),
        )


class TestPasswordHashing:
    async def test_maps_password_to_password_hash(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand(password="senha-secreta")

        await updater.update(id_, command)

        _, kwargs = users_repo.update.call_args
        update_command = kwargs["update_command"]
        assert update_command.password_hash != "senha-secreta"
        assert verify_password("senha-secreta", update_command.password_hash)

    async def test_does_not_carry_raw_password(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand(password="senha-secreta")

        await updater.update(id_, command)

        _, kwargs = users_repo.update.call_args
        assert not hasattr(kwargs["update_command"], "password")

    async def test_calls_hash_password_once(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)
        id_ = uuid.uuid4()
        command = UpdateUserCommand(password="senha-secreta")

        with patch(
            "app.modules.users.application.use_cases.update.hash_password",
            return_value="hashed",
        ) as mock_hash:
            await updater.update(id_, command)

        mock_hash.assert_called_once_with("senha-secreta")
        _, kwargs = users_repo.update.call_args
        assert kwargs["update_command"].password_hash == "hashed"


class TestUnitOfWork:
    async def test_returns_user_from_repository(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)

        result = await updater.update(
            uuid.uuid4(),
            UpdateUserCommand(name="X"),
        )

        assert result is user

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.update.return_value = user
        updater = UsersUpdater(uow)

        await updater.update(
            uuid.uuid4(),
            UpdateUserCommand(name="X"),
        )

        assert uow.entered
        assert uow.exited

    async def test_propagates_repository_error_and_exits_context(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        users_repo.update.side_effect = ValueError("não encontrado")
        updater = UsersUpdater(uow)

        with pytest.raises(ValueError, match="não encontrado"):
            await updater.update(
                uuid.uuid4(),
                UpdateUserCommand(name="X"),
            )

        assert uow.exited
        assert uow.exit_exc_type is ValueError

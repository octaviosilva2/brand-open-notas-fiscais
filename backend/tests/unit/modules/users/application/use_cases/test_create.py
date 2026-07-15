from unittest.mock import AsyncMock, patch

import pytest

from app.core.security.passwords import verify_password
from app.modules.users.application.dtos.commands import CreateUserCommand
from app.modules.users.application.use_cases.create import UsersCreator
from app.modules.users.domain.entities import User

from .conftest import FakeUsersUnitOfWork

_COMMAND = CreateUserCommand(
    email="novo@example.com",
    name="Novo",
    phone="11999999999",
    password="senha-secreta",
)


class TestCreate:
    async def test_maps_command_fields_to_new_user(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        await creator.create(_COMMAND)

        _, kwargs = users_repo.create.call_args
        new_user = kwargs["create_command"]
        assert new_user.email == "novo@example.com"
        assert new_user.name == "Novo"
        assert new_user.phone == "11999999999"

    async def test_new_user_is_active_by_default(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        await creator.create(_COMMAND)

        _, kwargs = users_repo.create.call_args
        assert kwargs["create_command"].is_active is True


class TestPasswordHashing:
    async def test_maps_password_to_password_hash(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        await creator.create(_COMMAND)

        _, kwargs = users_repo.create.call_args
        new_user = kwargs["create_command"]
        assert new_user.password_hash != "senha-secreta"
        assert verify_password("senha-secreta", new_user.password_hash)

    async def test_does_not_carry_raw_password(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        await creator.create(_COMMAND)

        _, kwargs = users_repo.create.call_args
        assert not hasattr(kwargs["create_command"], "password")

    async def test_calls_hash_password_once(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        with patch(
            "app.modules.users.application.use_cases.create.hash_password",
            return_value="hashed",
        ) as mock_hash:
            await creator.create(_COMMAND)

        mock_hash.assert_called_once_with("senha-secreta")
        _, kwargs = users_repo.create.call_args
        assert kwargs["create_command"].password_hash == "hashed"


class TestUnitOfWork:
    async def test_returns_user_from_repository(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        result = await creator.create(_COMMAND)

        assert result is user

    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
        user: User,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.return_value = user
        creator = UsersCreator(uow)

        await creator.create(_COMMAND)

        assert uow.entered
        assert uow.exited

    async def test_propagates_repository_error_and_exits_context(
        self,
        uow: FakeUsersUnitOfWork,
        users_repo: AsyncMock,
    ):
        users_repo.get_by_email_or_none.return_value = None
        users_repo.create.side_effect = ValueError("email duplicado")
        creator = UsersCreator(uow)

        with pytest.raises(ValueError, match="email duplicado"):
            await creator.create(_COMMAND)

        assert uow.exited
        assert uow.exit_exc_type is ValueError

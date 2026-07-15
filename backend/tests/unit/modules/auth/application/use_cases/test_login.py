import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import decode_access_token, decode_refresh_token
from app.core.security.passwords import hash_password
from app.modules.auth.application.dtos.commands import LoginCommand
from app.modules.auth.application.dtos.results import TokenPair
from app.modules.auth.application.use_cases.login import AuthLogin
from app.modules.auth.domain.entities import Credentials

from .conftest import FakeAuthUnitOfWork

_COMMAND = LoginCommand(email="user@example.com", password="senha1234")


class TestLoginSuccess:
    async def test_returns_token_pair(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        result = await AuthLogin(uow).login(_COMMAND)

        assert isinstance(result, TokenPair)
        assert result.access_token
        assert result.refresh_token

    async def test_access_token_has_subject_and_type(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        result = await AuthLogin(uow).login(_COMMAND)

        claims = decode_access_token(result.access_token)
        assert claims["sub"] == str(credentials.id)
        assert claims["type"] == "access"

    async def test_refresh_token_has_subject_and_type(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        result = await AuthLogin(uow).login(_COMMAND)

        claims = decode_refresh_token(result.refresh_token)
        assert claims["sub"] == str(credentials.id)
        assert claims["type"] == "refresh"

    async def test_looks_up_credentials_by_email(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        await AuthLogin(uow).login(_COMMAND)

        credentials_repo.get_credentials_by_email.assert_awaited_once_with(
            "user@example.com"
        )


class TestLoginFailure:
    async def test_unknown_email_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
    ):
        credentials_repo.get_credentials_by_email.return_value = None

        with pytest.raises(UnauthorizedError):
            await AuthLogin(uow).login(_COMMAND)

    async def test_wrong_password_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        with pytest.raises(UnauthorizedError):
            await AuthLogin(uow).login(
                LoginCommand(email="user@example.com", password="errada")
            )

    async def test_inactive_user_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
    ):
        inactive = Credentials(
            id=uuid.uuid4(),
            password_hash=hash_password("senha1234"),
            is_active=False,
        )
        credentials_repo.get_credentials_by_email.return_value = inactive

        with pytest.raises(UnauthorizedError):
            await AuthLogin(uow).login(_COMMAND)


class TestLoginUnitOfWork:
    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_email.return_value = credentials

        await AuthLogin(uow).login(_COMMAND)

        assert uow.entered
        assert uow.exited

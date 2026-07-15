import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.security.passwords import hash_password
from app.modules.auth.application.dtos.commands import RefreshCommand
from app.modules.auth.application.dtos.results import TokenPair
from app.modules.auth.application.use_cases.refresh import AuthRefresher
from app.modules.auth.domain.entities import Credentials

from .conftest import FakeAuthUnitOfWork


class TestRefreshSuccess:
    async def test_returns_new_token_pair(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_id.return_value = credentials
        token = create_refresh_token(TokenIdentity(subject=credentials.id))

        result = await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))

        assert isinstance(result, TokenPair)
        assert decode_access_token(result.access_token)["sub"] == str(credentials.id)
        assert decode_refresh_token(result.refresh_token)["sub"] == str(credentials.id)

    async def test_looks_up_credentials_by_id(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_id.return_value = credentials
        token = create_refresh_token(TokenIdentity(subject=credentials.id))

        await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))

        credentials_repo.get_credentials_by_id.assert_awaited_once_with(credentials.id)


class TestRefreshFailure:
    async def test_invalid_token_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
    ):
        with pytest.raises(UnauthorizedError):
            await AuthRefresher(uow).refresh(RefreshCommand(refresh_token="not-a-jwt"))

    async def test_access_token_as_refresh_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        token = create_access_token(TokenIdentity(subject=credentials.id))

        with pytest.raises(UnauthorizedError):
            await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))

    async def test_unknown_user_raises_unauthorized(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
    ):
        credentials_repo.get_credentials_by_id.return_value = None
        token = create_refresh_token(TokenIdentity(subject=uuid.uuid4()))

        with pytest.raises(UnauthorizedError):
            await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))

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
        credentials_repo.get_credentials_by_id.return_value = inactive
        token = create_refresh_token(TokenIdentity(subject=inactive.id))

        with pytest.raises(UnauthorizedError):
            await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))


class TestRefreshUnitOfWork:
    async def test_enters_and_exits_unit_of_work(
        self,
        uow: FakeAuthUnitOfWork,
        credentials_repo: AsyncMock,
        credentials: Credentials,
    ):
        credentials_repo.get_credentials_by_id.return_value = credentials
        token = create_refresh_token(TokenIdentity(subject=credentials.id))

        await AuthRefresher(uow).refresh(RefreshCommand(refresh_token=token))

        assert uow.entered
        assert uow.exited

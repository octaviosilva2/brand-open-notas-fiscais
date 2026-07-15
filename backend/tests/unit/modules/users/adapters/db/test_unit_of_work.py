from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.users.adapters.db.repository import UsersRepository
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork


def make_uow() -> tuple[UsersUnitOfWork, AsyncMock]:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    factory = MagicMock(return_value=session)
    uow = UsersUnitOfWork(session_factory=factory)
    return uow, session


# --- __init__ ---


class TestInit:
    def test_stores_session_factory(self):
        factory = MagicMock()
        uow = UsersUnitOfWork(session_factory=factory)

        assert uow._session_factory is factory

    def test_users_repository_is_initially_none(self):
        uow = UsersUnitOfWork(session_factory=MagicMock())

        assert uow._users is None


# --- users property ---


class TestUsersProperty:
    def test_raises_runtime_error_before_entering_context(self):
        uow = UsersUnitOfWork(session_factory=MagicMock())

        with pytest.raises(RuntimeError):
            _ = uow.users

    async def test_returns_repository_after_entering_context(self):
        uow, _ = make_uow()

        async with uow:
            assert uow.users is not None

    async def test_returns_users_repository_instance(self):
        uow, _ = make_uow()

        async with uow:
            assert isinstance(uow.users, UsersRepository)


# --- __aenter__ ---


class TestAenter:
    async def test_initializes_users_repository(self):
        uow, _ = make_uow()

        async with uow:
            assert uow._users is not None

    async def test_returns_self(self):
        uow, _ = make_uow()

        result = await uow.__aenter__()

        assert result is uow
        await uow.__aexit__(None, None, None)

    async def test_calls_session_factory(self):
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        factory = MagicMock(return_value=session)
        uow = UsersUnitOfWork(session_factory=factory)

        async with uow:
            pass

        factory.assert_called_once()


# --- __aexit__ ---


class TestAexit:
    async def test_resets_users_repository_to_none_after_exit(self):
        uow, _ = make_uow()

        async with uow:
            pass

        assert uow._users is None

    async def test_commits_when_no_exception(self):
        uow, session = make_uow()

        async with uow:
            pass

        session.commit.assert_awaited_once()

    async def test_rolls_back_on_exception(self):
        uow, session = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        session.rollback.assert_awaited_once()

    async def test_does_not_commit_on_exception(self):
        uow, session = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        session.commit.assert_not_awaited()

    async def test_closes_session_after_exit(self):
        uow, session = make_uow()

        async with uow:
            pass

        session.close.assert_awaited_once()

    async def test_resets_users_to_none_on_exception(self):
        uow, _ = make_uow()

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("erro")

        assert uow._users is None

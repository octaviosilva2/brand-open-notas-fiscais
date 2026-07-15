import uuid
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock

import pytest

from app.core.actors.user import UserActor
from app.core.exceptions import UnauthorizedError
from app.modules.users.adapters.http.dependencies import (
    get_current_actor,
    get_pagination_filters,
)
from app.modules.users.adapters.http.schemas import UsersPaginationFilters
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import User


class FakeUsersUnitOfWork:
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


def make_user(*, is_active: bool = True) -> User:
    from datetime import datetime

    now = datetime(2026, 6, 11, 12, 0, 0)
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        name="Fulano",
        phone="11999999999",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def users_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def uow(users_repo: AsyncMock) -> FakeUsersUnitOfWork:
    return FakeUsersUnitOfWork(users_repo)


class TestGetCurrentActor:
    async def test_returns_user_actor_when_user_is_active(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        user = make_user(is_active=True)
        users_repo.get_by_id_or_none.return_value = user
        user_id = uuid.uuid4()

        result = await get_current_actor(user_id, uow)

        assert isinstance(result, UserActor)
        assert result.user_id == user.id

    async def test_passes_user_id_to_repository(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        user = make_user()
        users_repo.get_by_id_or_none.return_value = user
        user_id = uuid.uuid4()

        await get_current_actor(user_id, uow)

        users_repo.get_by_id_or_none.assert_awaited_once_with(user_id)

    async def test_raises_unauthorized_when_user_not_found(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        users_repo.get_by_id_or_none.return_value = None

        with pytest.raises(UnauthorizedError):
            await get_current_actor(uuid.uuid4(), uow)

    async def test_raises_unauthorized_when_user_is_inactive(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        users_repo.get_by_id_or_none.return_value = make_user(is_active=False)

        with pytest.raises(UnauthorizedError):
            await get_current_actor(uuid.uuid4(), uow)

    async def test_unauthorized_message_when_not_found(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        users_repo.get_by_id_or_none.return_value = None

        with pytest.raises(UnauthorizedError, match="inativo ou não encontrado"):
            await get_current_actor(uuid.uuid4(), uow)

    async def test_opens_and_closes_unit_of_work(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        users_repo.get_by_id_or_none.return_value = make_user()

        await get_current_actor(uuid.uuid4(), uow)

        assert uow.entered
        assert uow.exited

    async def test_uow_closed_when_user_not_found(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        users_repo.get_by_id_or_none.return_value = None

        with pytest.raises(UnauthorizedError):
            await get_current_actor(uuid.uuid4(), uow)

        assert uow.exited

    async def test_returns_actor_with_user_id_from_entity(
        self, uow: FakeUsersUnitOfWork, users_repo: AsyncMock
    ):
        user = make_user()
        users_repo.get_by_id_or_none.return_value = user

        result = await get_current_actor(uuid.uuid4(), uow)

        assert result.user_id == user.id


class TestGetPaginationFilters:
    def test_returns_user_filters_instance(self):
        params = UsersPaginationFilters()

        result = get_pagination_filters(params)

        assert isinstance(result, UserFilters)

    def test_passes_q_correctly(self):
        params = UsersPaginationFilters(q="fulano")

        result = get_pagination_filters(params)

        assert result.q == "fulano"

    def test_passes_is_active_true(self):
        params = UsersPaginationFilters(is_active=True)

        result = get_pagination_filters(params)

        assert result.is_active is True

    def test_passes_is_active_false(self):
        params = UsersPaginationFilters(is_active=False)

        result = get_pagination_filters(params)

        assert result.is_active is False

    def test_passes_is_active_none(self):
        params = UsersPaginationFilters(is_active=None)

        result = get_pagination_filters(params)

        assert result.is_active is None

    def test_passes_q_none(self):
        params = UsersPaginationFilters(q=None)

        result = get_pagination_filters(params)

        assert result.q is None

    def test_passes_both_fields(self):
        params = UsersPaginationFilters(q="maria", is_active=False)

        result = get_pagination_filters(params)

        assert result.q == "maria"
        assert result.is_active is False

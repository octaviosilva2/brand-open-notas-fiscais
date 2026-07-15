import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.users.adapters.db.models import User as UserModel
from app.modules.users.adapters.db.repository import UsersRepository
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import User

# --- Helpers ---


def make_user_model(
    *,
    id_: uuid.UUID | None = None,
    email: str = "user@example.com",
    name: str = "Fulano",
    phone: str = "11999999999",
    is_active: bool = True,
) -> UserModel:
    now = datetime(2026, 6, 11, 12, 0, 0)
    model = UserModel(
        id=id_ or uuid.uuid4(),
        email=email,
        name=name,
        phone=phone,
        is_active=is_active,
        password_hash="hashed",
    )
    model.created_at = now
    model.updated_at = now
    return model


def make_execute_result(row: UserModel | None) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.one_or_none.return_value = row
    return result


# --- Fixtures ---


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> UsersRepository:
    return UsersRepository(session)


# --- get_by_email_or_none ---


class TestGetByEmailOrNone:
    async def test_returns_user_entity_when_found(self, repo, session):
        id_ = uuid.uuid4()
        model = make_user_model(id_=id_, email="found@example.com")
        session.execute.return_value = make_execute_result(model)

        result = await repo.get_by_email_or_none("found@example.com")

        assert result is not None
        assert result.id == id_
        assert result.email == "found@example.com"

    async def test_returns_none_when_not_found(self, repo, session):
        session.execute.return_value = make_execute_result(None)

        result = await repo.get_by_email_or_none("missing@example.com")

        assert result is None

    async def test_executes_select_on_user_model(self, repo, session):
        session.execute.return_value = make_execute_result(None)

        await repo.get_by_email_or_none("any@example.com")

        session.execute.assert_awaited_once()
        stmt = session.execute.call_args.args[0]
        assert isinstance(stmt, sa.Select)


# --- get_by_email ---


class TestGetByEmail:
    async def test_returns_user_entity_when_found(self, repo, session):
        id_ = uuid.uuid4()
        model = make_user_model(id_=id_, email="user@example.com")
        session.execute.return_value = make_execute_result(model)

        result = await repo.get_by_email("user@example.com")

        assert result.id == id_
        assert result.email == "user@example.com"

    async def test_raises_not_found_when_missing(self, repo, session):
        session.execute.return_value = make_execute_result(None)

        with pytest.raises(NotFoundError):
            await repo.get_by_email("missing@example.com")

    async def test_not_found_message_contains_email(self, repo, session):
        session.execute.return_value = make_execute_result(None)

        with pytest.raises(NotFoundError, match=r"missing@example.com"):
            await repo.get_by_email("missing@example.com")


# --- _to_entity ---


class TestToEntity:
    def test_maps_all_fields_to_user_entity(self, repo):
        id_ = uuid.uuid4()
        now = datetime(2026, 6, 11, 12, 0, 0)
        model = make_user_model(
            id_=id_,
            email="map@example.com",
            name="Ciclano",
            phone="21988887777",
            is_active=False,
        )
        model.created_at = now
        model.updated_at = now

        entity = repo._to_entity(model)

        assert entity == User(
            id=id_,
            email="map@example.com",
            name="Ciclano",
            phone="21988887777",
            is_active=False,
            created_at=now,
            updated_at=now,
        )

    def test_returns_user_instance(self, repo):
        model = make_user_model()

        entity = repo._to_entity(model)

        assert isinstance(entity, User)


# --- _apply_filters ---


class TestApplyFilters:
    def test_q_filter_adds_ilike_on_email(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q="fulano", is_active=None)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        # sem dialect PostgreSQL, ilike compila como lower(...) LIKE lower(...)
        assert "%fulano%" in compiled

    def test_is_active_true_adds_filter(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q=None, is_active=True)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "is_active" in compiled
        assert "true" in compiled.lower()

    def test_is_active_false_adds_filter(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q=None, is_active=False)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "is_active" in compiled
        assert "false" in compiled.lower()

    def test_is_active_none_does_not_filter(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q=None, is_active=None)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        # is_active aparece no SELECT, mas não deve aparecer no WHERE
        assert "WHERE" not in compiled

    def test_q_none_does_not_add_ilike(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q=None, is_active=None)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "ilike" not in compiled.lower()

    def test_all_none_filters_produce_no_where_clause(self, repo):
        stmt = sa.select(UserModel)
        filters = UserFilters(q=None, is_active=None)

        result = repo._apply_filters(stmt, filters)
        compiled = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE" not in compiled

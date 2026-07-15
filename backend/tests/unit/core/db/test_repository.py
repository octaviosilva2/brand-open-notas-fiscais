import dataclasses
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.core.pagination.params import Page, PageParams
from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset

# --- Doubles sintéticos (não são coletados: não começam com "Test") ---


class ModelBase(DeclarativeBase):
    """Base isolada para não poluir o metadata do app."""


class Thing(ModelBase):
    __tablename__ = "things"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


@dataclasses.dataclass(frozen=True, slots=True)
class ThingEntity:
    id: uuid.UUID
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class ThingFilters:
    name: str | None = None


@dataclasses.dataclass(frozen=True, slots=True)
class NewThing(BaseCreateCommand):
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class UpdateThing(BaseUpdateCommand):
    name: str | Unset = UNSET


# `ModelBase` is intentionally isolated from the app `Base` to avoid metadata
# pollution in tests. This technically violates the `ModelT: Base` bound, so we
# suppress the resulting mypy error here.
class FakeRepository(
    BaseRepository[Thing, ThingEntity, ThingFilters]  # type: ignore[type-var]
):
    model = Thing
    filters_type = ThingFilters

    def _to_entity(self, row: Thing) -> ThingEntity:
        return ThingEntity(id=row.id, name=row.name)


class SpyRepository(FakeRepository):
    """Registra os filtros recebidos por `_apply_filters`."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.applied_filters: ThingFilters | None = None

    def _apply_filters(
        self, stmt: sa.Select[Any], filters: ThingFilters
    ) -> sa.Select[Any]:
        self.applied_filters = filters
        return stmt


# --- Helpers e fixtures ---


def make_execute_result(rows: list[Thing]) -> MagicMock:
    """Simula o retorno de `session.execute` para consultas paginadas."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(session: AsyncMock) -> FakeRepository:
    return FakeRepository(session)


# --- get_by_id_or_none ---


async def test_get_by_id_or_none_returns_entity_when_found(repo, session):
    id_ = uuid.uuid7()
    session.get.return_value = Thing(id=id_, name="bar")

    result = await repo.get_by_id_or_none(id_)

    assert result == ThingEntity(id=id_, name="bar")
    session.get.assert_awaited_once_with(Thing, id_)


async def test_get_by_id_or_none_returns_none_when_missing(repo, session):
    id_ = uuid.uuid7()
    session.get.return_value = None

    assert await repo.get_by_id_or_none(id_) is None
    session.get.assert_awaited_once_with(Thing, id_)


# --- get_by_id ---


async def test_get_by_id_returns_entity_when_found(repo, session):
    id_ = uuid.uuid7()
    session.get.return_value = Thing(id=id_, name="z")

    assert await repo.get_by_id(id_) == ThingEntity(id=id_, name="z")


async def test_get_by_id_raises_not_found_when_missing(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo.get_by_id(uuid.uuid7())


# --- create ---


async def test_create_adds_model_flushes_and_returns_entity(repo, session):
    entity = await repo.create(NewThing(name="foo"))

    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert isinstance(added, Thing)
    assert added.name == "foo"

    session.flush.assert_awaited_once()
    assert entity == ThingEntity(id=added.id, name="foo")


# --- update ---


async def test_update_applies_only_defined_values(repo, session):
    id_ = uuid.uuid7()
    existing = Thing(id=id_, name="old")
    session.get.return_value = existing

    result = await repo.update(id_, UpdateThing(name="new"))

    assert existing.name == "new"
    session.flush.assert_awaited_once()
    assert result == ThingEntity(id=id_, name="new")


async def test_update_with_all_unset_changes_nothing_but_flushes(repo, session):
    id_ = uuid.uuid7()
    existing = Thing(id=id_, name="old")
    session.get.return_value = existing

    result = await repo.update(id_, UpdateThing())

    assert existing.name == "old"
    session.flush.assert_awaited_once()
    assert result == ThingEntity(id=id_, name="old")


async def test_update_raises_not_found_when_missing(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo.update(uuid.uuid7(), UpdateThing(name="x"))


# --- delete ---


async def test_delete_succeeds_when_row_deleted(repo, session):
    result_mock = MagicMock()
    result_mock.rowcount = 1
    session.execute.return_value = result_mock

    await repo.delete(uuid.uuid7())

    session.execute.assert_awaited_once()
    stmt = session.execute.call_args.args[0]
    assert isinstance(stmt, sa.Delete)


async def test_delete_raises_not_found_when_no_row(repo, session):
    result_mock = MagicMock()
    result_mock.rowcount = 0
    session.execute.return_value = result_mock

    with pytest.raises(NotFoundError):
        await repo.delete(uuid.uuid7())


# --- paginate ---


async def test_paginate_returns_page_with_items_and_total(repo, session):
    id1, id2 = uuid.uuid7(), uuid.uuid7()
    rows = [Thing(id=id1, name="a"), Thing(id=id2, name="b")]
    session.scalar.return_value = 2
    session.execute.return_value = make_execute_result(rows)

    page = await repo.paginate(PageParams(page=1, page_size=20))

    assert page == Page(
        items=[ThingEntity(id=id1, name="a"), ThingEntity(id=id2, name="b")],
        total=2,
        page=1,
        page_size=20,
    )


async def test_paginate_total_zero_when_scalar_none(repo, session):
    session.scalar.return_value = None
    session.execute.return_value = make_execute_result([])

    page = await repo.paginate(PageParams())

    assert page.total == 0


async def test_paginate_uses_default_filters_when_none(session):
    repo = SpyRepository(session)
    session.scalar.return_value = 0
    session.execute.return_value = make_execute_result([])

    await repo.paginate(PageParams(), filters=None)

    assert repo.applied_filters == ThingFilters()


async def test_paginate_passes_filters_to_apply_filters(session):
    repo = SpyRepository(session)
    session.scalar.return_value = 0
    session.execute.return_value = make_execute_result([])
    filters = ThingFilters(name="x")

    await repo.paginate(PageParams(), filters=filters)

    assert repo.applied_filters is filters


async def test_paginate_applies_offset_and_limit_for_page_2(repo, session):
    session.scalar.return_value = 0
    session.execute.return_value = make_execute_result([])

    await repo.paginate(PageParams(page=2, page_size=10))

    stmt = session.execute.call_args.args[0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT 10" in compiled
    assert "OFFSET 10" in compiled


# --- helpers e _apply_filters padrão ---


def test_default_apply_filters_returns_stmt_unchanged(repo):
    stmt = sa.select(Thing)

    assert repo._apply_filters(stmt, ThingFilters()) is stmt


async def test_get_model_by_id_raises_not_found_when_missing(repo, session):
    session.get.return_value = None

    with pytest.raises(NotFoundError):
        await repo._get_model_by_id(uuid.uuid7())

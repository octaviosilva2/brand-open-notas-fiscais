import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_connection(test_engine):
    async with test_engine.connect() as conn:
        await conn.begin()
        yield conn
        await conn.rollback()


@pytest.fixture
def test_session_factory(db_connection):
    return async_sessionmaker(
        db_connection,
        class_=AsyncSession,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )


@pytest.fixture
async def client(test_session_factory):
    from app.main import app
    from app.modules.auth.adapters.db.factories import (
        make_unit_of_work as make_auth_uow,
    )
    from app.modules.auth.adapters.db.unit_of_work import AuthUnitOfWork
    from app.modules.users.adapters.db.factories import make_unit_of_work
    from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork

    def make_test_uow() -> UsersUnitOfWork:
        return UsersUnitOfWork(session_factory=test_session_factory)

    def make_test_auth_uow() -> AuthUnitOfWork:
        return AuthUnitOfWork(session_factory=test_session_factory)

    from app.modules.clients.adapters.db.factories import (
        make_unit_of_work as make_clients_uow,
    )
    from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork
    from app.modules.invoices.adapters.db.factories import (
        make_unit_of_work as make_invoices_uow,
    )
    from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork
    from app.modules.recurrences.adapters.db.factories import (
        make_unit_of_work as make_recurrences_uow,
    )
    from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork

    def make_test_clients_uow() -> ClientsUnitOfWork:
        return ClientsUnitOfWork(session_factory=test_session_factory)

    def make_test_recurrences_uow() -> RecurrencesUnitOfWork:
        return RecurrencesUnitOfWork(session_factory=test_session_factory)

    def make_test_invoices_uow() -> InvoicesUnitOfWork:
        return InvoicesUnitOfWork(session_factory=test_session_factory)

    app.dependency_overrides[make_unit_of_work] = make_test_uow
    app.dependency_overrides[make_auth_uow] = make_test_auth_uow
    app.dependency_overrides[make_clients_uow] = make_test_clients_uow
    app.dependency_overrides[make_recurrences_uow] = make_test_recurrences_uow
    app.dependency_overrides[make_invoices_uow] = make_test_invoices_uow
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()

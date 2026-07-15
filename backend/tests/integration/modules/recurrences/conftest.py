# tests/integration/modules/recurrences/conftest.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import TokenIdentity, create_access_token
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel
from tests.integration.modules.users.conftest import insert_user


async def insert_client(
    conn: AsyncConnection, document: str = "12345678901"
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(ClientModel).values(
            id=uid,
            document=document,
            name="Cliente Teste",
            municipal_registration=None,
            phone=None,
            email=None,
            zip_code=None,
            street=None,
            number=None,
            complement=None,
            neighborhood=None,
            ibge_city_code=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


async def insert_recurrence(
    conn: AsyncConnection,
    client_id: uuid.UUID,
    *,
    day_of_month: int = 15,
    is_active: bool = True,
    end_date: date | None = None,
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(RecurrenceModel).values(
            id=uid,
            client_id=client_id,
            description="Serviço mensal",
            amount=Decimal("1500.00"),
            day_of_month=day_of_month,
            start_date=date(2026, 1, 1),
            end_date=end_date,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_client_id(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_client(db_connection)


@pytest.fixture
async def test_recurrence_id(
    db_connection: AsyncConnection, test_client_id: uuid.UUID
) -> uuid.UUID:
    return await insert_recurrence(db_connection, test_client_id)


@pytest.fixture
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_user(
        db_connection,
        name="Teste Recorrencias",
        email="recorrencias@test.com",
        phone="11999990003",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}

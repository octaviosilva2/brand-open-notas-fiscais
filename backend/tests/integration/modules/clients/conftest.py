# tests/integration/modules/clients/conftest.py
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import TokenIdentity, create_access_token
from app.modules.clients.adapters.db.models import Client as ClientModel
from tests.integration.modules.users.conftest import insert_user


async def insert_client(
    db_connection: AsyncConnection,
    *,
    document: str = "12345678901",
    name: str = "Cliente Teste",
    is_active: bool = True,
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await db_connection.execute(
        insert(ClientModel).values(
            id=uid,
            document=document,
            name=name,
            municipal_registration=None,
            phone=None,
            email=None,
            zip_code=None,
            street=None,
            number=None,
            complement=None,
            neighborhood=None,
            ibge_city_code=None,
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
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_user(
        db_connection,
        name="Teste Clientes",
        email="clientes@test.com",
        phone="11999990002",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import TokenIdentity, create_access_token
from app.core.security.passwords import hash_password
from app.modules.users.adapters.db.models import User as UserModel


async def insert_user(
    db_connection: AsyncConnection,
    *,
    name: str = "Teste",
    email: str,
    phone: str,
    password: str = "senha1234",
    is_active: bool = True,
) -> uuid.UUID:
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await db_connection.execute(
        insert(UserModel).values(
            id=uid,
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_user(
        db_connection,
        name="Teste Integração",
        email="integracao@test.com",
        phone="11999990001",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}

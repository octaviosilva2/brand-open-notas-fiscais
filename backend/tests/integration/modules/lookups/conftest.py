# tests/integration/modules/lookups/conftest.py
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import TokenIdentity, create_access_token
from tests.integration.modules.users.conftest import insert_user


@pytest.fixture
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    return await insert_user(
        db_connection,
        name="Teste Lookups",
        email="lookups@test.com",
        phone="11999990009",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}

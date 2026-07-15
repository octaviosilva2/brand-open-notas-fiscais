import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from tests.integration.modules.users.conftest import insert_user

LOGIN_EMAIL = "login@test.com"
LOGIN_PASSWORD = "senha1234"


@pytest.fixture
async def login_user(db_connection: AsyncConnection) -> uuid.UUID:
    """Cria um usuário ativo com email e senha conhecidos para os testes de login."""
    return await insert_user(
        db_connection,
        name="Usuário Login",
        email=LOGIN_EMAIL,
        phone="11990001111",
        password=LOGIN_PASSWORD,
    )

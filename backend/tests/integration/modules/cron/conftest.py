# tests/integration/modules/cron/conftest.py
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


async def insert_client_and_recurrence(
    conn: AsyncConnection,
    *,
    document: str = "10000000001",
    day_of_month: int = 15,
) -> tuple[uuid.UUID, uuid.UUID]:
    """Insere cliente e recorrência de teste, retornando seus IDs."""
    client_id = uuid.uuid7()
    rec_id = uuid.uuid7()
    now = datetime.now(tz=UTC)

    await conn.execute(
        insert(ClientModel).values(
            id=client_id,
            document=document,
            name=f"Cliente {document}",
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
    await conn.execute(
        insert(RecurrenceModel).values(
            id=rec_id,
            client_id=client_id,
            description="Serviço teste",
            amount=Decimal("500.00"),
            day_of_month=day_of_month,
            start_date=date(2026, 1, 1),
            end_date=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    return client_id, rec_id


@pytest.fixture
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    """Cria usuário de teste para autenticação."""
    return await insert_user(
        db_connection,
        name="Teste Cron",
        email="cron@test.com",
        phone="11999990005",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    """Gera token JWT para o usuário de teste."""
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Headers de autorização para as requisições de teste."""
    return {"Authorization": f"Bearer {auth_token}"}

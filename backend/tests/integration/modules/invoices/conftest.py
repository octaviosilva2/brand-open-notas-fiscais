# tests/integration/modules/invoices/conftest.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import TokenIdentity, create_access_token
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.invoices.adapters.db.models import Invoice as InvoiceModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel
from tests.integration.modules.users.conftest import insert_user


async def _insert_client(
    conn: AsyncConnection, document: str = "12345678901"
) -> uuid.UUID:
    """Insere um cliente de teste no banco."""
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(ClientModel).values(
            id=uid,
            document=document,
            name="Cliente NF",
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


async def _insert_recurrence(conn: AsyncConnection, client_id: uuid.UUID) -> uuid.UUID:
    """Insere uma recorrência de teste vinculada ao cliente."""
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(RecurrenceModel).values(
            id=uid,
            client_id=client_id,
            description="Serviço",
            amount=Decimal("1500.00"),
            day_of_month=15,
            start_date=date(2026, 1, 1),
            end_date=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


async def insert_invoice(
    conn: AsyncConnection,
    recurrence_id: uuid.UUID,
    client_id: uuid.UUID,
    *,
    status: str = "success",
    scheduled_date: date = date(2026, 6, 15),
    xml_sent: str | None = None,
    pdf_url: str | None = None,
    nf_number: str | None = "NF001",
) -> uuid.UUID:
    """Insere uma invoice de teste com os parâmetros fornecidos."""
    uid = uuid.uuid7()
    now = datetime.now(tz=UTC)
    await conn.execute(
        insert(InvoiceModel).values(
            id=uid,
            recurrence_id=recurrence_id,
            client_id=client_id,
            scheduled_date=scheduled_date,
            amount=Decimal("1500.00"),
            description="Serviço",
            status=status,
            n_dps=1,
            protocol="PROT001",
            nf_number=nf_number,
            pdf_url=pdf_url,
            xml_sent=xml_sent,
            xml_response=None,
            error_message=None,
            emission_date=now if status == "success" else None,
            created_at=now,
            updated_at=now,
        )
    )
    return uid


@pytest.fixture
async def test_user(db_connection: AsyncConnection) -> uuid.UUID:
    """Cria usuário de teste para autenticação."""
    return await insert_user(
        db_connection,
        name="Teste Invoices",
        email="invoices@test.com",
        phone="11999990004",
    )


@pytest.fixture
def auth_token(test_user: uuid.UUID) -> str:
    """Gera token JWT para o usuário de teste."""
    return create_access_token(TokenIdentity(subject=test_user))


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Headers de autorização para as requisições de teste."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def test_ids(db_connection: AsyncConnection) -> dict:
    """Cria cliente, recorrência e invoice de teste, retornando seus IDs."""
    client_id = await _insert_client(db_connection)
    rec_id = await _insert_recurrence(db_connection, client_id)
    inv_id = await insert_invoice(
        db_connection,
        rec_id,
        client_id,
        xml_sent="<xml>test</xml>",
        pdf_url="http://pdf.example.com/nf001.pdf",
    )
    return {"client_id": client_id, "recurrence_id": rec_id, "invoice_id": inv_id}

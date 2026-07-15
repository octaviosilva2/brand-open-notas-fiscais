"""
Seed de dados de teste para emissão de notas fiscais.

Cria clientes e recorrências que disparam no dia 15 do mês,
permitindo testar o cron de emissão imediatamente.

Uso:
    uv run python -m scripts.seed.test_data
"""

import asyncio
import sys
import os
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.db.session import db
from app.core.exceptions import ConflictError
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.clients.application.dtos.commands import CreateClientCommand
from app.modules.clients.application.use_cases.clients_creator import ClientsCreator
from app.modules.recurrences.adapters.db.factories import (
    make_unit_of_work as make_recurrences_uow,
)
from app.modules.recurrences.application.dtos.commands import CreateRecurrenceCommand
from app.modules.recurrences.application.use_cases.recurrences_creator import (
    RecurrencesCreator,
)

CLIENTS: list[CreateClientCommand] = [
    CreateClientCommand(
        document="52998224725",  # CPF (PF)
        name="João da Silva Santos",
        municipal_registration=None,
        phone="48999990001",
        email="joao.santos@email.com",
        zip_code="88010001",
        street="Rua Felipe Schmidt",
        number="515",
        complement="Apto 301",
        neighborhood="Centro",
        ibge_city_code="4205407",  # Florianópolis/SC
    ),
    CreateClientCommand(
        document="11222333000181",  # CNPJ (PJ)
        name="Empresa Teste Serviços LTDA",
        municipal_registration="123456",
        phone="48988880002",
        email="contato@empresateste.com.br",
        zip_code="88015050",
        street="Av. Hercílio Luz",
        number="100",
        complement=None,
        neighborhood="Centro",
        ibge_city_code="4205407",  # Florianópolis/SC
    ),
    CreateClientCommand(
        document="34028316000103",  # CNPJ (PJ)
        name="Clínica ABC Saúde ME",
        municipal_registration="654321",
        phone="11977770003",
        email="clinica@abcsaude.com.br",
        zip_code="01310100",
        street="Av. Paulista",
        number="1000",
        complement="Sala 52",
        neighborhood="Bela Vista",
        ibge_city_code="3550308",  # São Paulo/SP
    ),
]


async def seed_clients() -> dict[str, object]:
    """Cria os clientes de teste e retorna mapa document→client."""
    creator = ClientsCreator(uow=make_clients_uow())
    created: dict[str, object] = {}

    for cmd in CLIENTS:
        try:
            client = await creator.create(cmd)
            print(f"  ✓ Cliente criado: {client.name} ({client.document})")
            created[cmd.document] = client
        except ConflictError:
            # Já existe — busca para usar nas recorrências
            async with make_clients_uow() as uow:
                client = await uow.clients.get_by_document_or_none(cmd.document)
            print(f"  ~ Cliente já existe: {cmd.name} ({cmd.document})")
            created[cmd.document] = client

    return created


async def seed_recurrences(clients: dict[str, object]) -> None:
    """Cria recorrências de teste vinculadas aos clientes."""
    joao = clients["52998224725"]
    empresa = clients["11222333000181"]
    clinica = clients["34028316000103"]

    recurrences: list[CreateRecurrenceCommand] = [
        CreateRecurrenceCommand(
            client_id=joao.id,
            description="Consultoria em desenvolvimento de software - mensal",
            amount=Decimal("350.00"),
            day_of_month=16,
            start_date=date(2026, 1, 1),
        ),
        CreateRecurrenceCommand(
            client_id=empresa.id,
            description="Licença de sistema de gestão - plano mensal",
            amount=Decimal("1200.00"),
            day_of_month=15,
            start_date=date(2026, 1, 1),
        ),
        CreateRecurrenceCommand(
            client_id=clinica.id,
            description="Suporte técnico e manutenção de infraestrutura",
            amount=Decimal("480.00"),
            day_of_month=1,
            start_date=date(2026, 1, 1),
        ),
    ]

    creator = RecurrencesCreator(uow=make_recurrences_uow())
    for cmd in recurrences:
        rec = await creator.create(cmd)
        client = next(c for c in clients.values() if c.id == cmd.client_id)
        print(
            f"  ✓ Recorrência criada: {client.name} — dia {rec.day_of_month} "
            f"— R$ {rec.amount}"
        )


async def main() -> None:
    db.init()

    print("\n=== Clientes ===")
    clients = await seed_clients()

    print("\n=== Recorrências ===")
    await seed_recurrences(clients)

    print("\nSeed concluído.")
    print(
        "As recorrências com dia=15 disparam hoje (15/jun). "
        "Rode o cron com POST /cron/run para testar a emissão."
    )

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

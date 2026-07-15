"""
Cria o usuário administrador inicial no banco de dados.

Uso:
    python -m scripts.seed.initial_user

Variáveis de ambiente (opcionais — usam os defaults abaixo se não definidas):
    SEED_USER_NAME
    SEED_USER_EMAIL
    SEED_USER_PHONE
    SEED_USER_PASSWORD
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.db.session import db
from app.modules.users.adapters.db.unit_of_work import UsersUnitOfWork
from app.modules.users.application.dtos.commands import CreateUserCommand
from app.modules.users.application.use_cases.create import UsersCreator


async def main() -> None:
    db.init()

    command = CreateUserCommand(
        name=os.getenv("SEED_USER_NAME", "Administrador"),
        email=os.getenv("SEED_USER_EMAIL", "admin@gmail.com"),
        phone=os.getenv("SEED_USER_PHONE", "00000000000"),
        password=os.getenv("SEED_USER_PASSWORD", "admin123"),
    )

    uow = UsersUnitOfWork(session_factory=db.create_session)
    creator = UsersCreator(uow=uow)

    user = await creator.create(command)

    print(f"Usuário criado: {user.name} <{user.email}> (id={user.id})")

    await db.close()


if __name__ == "__main__":
    asyncio.run(main())

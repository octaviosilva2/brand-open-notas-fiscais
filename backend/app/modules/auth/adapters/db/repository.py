import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import Credentials
from app.modules.users.adapters.db.models import User as UserModel


class AuthRepository:
    """Repositório de credenciais. Lê a tabela de usuários e devolve apenas os
    campos necessários à autenticação, sem expor o model SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_credentials_by_email(self, email: str) -> Credentials | None:
        """Obtém as credenciais de um usuário pelo email. `None` se não encontrado."""
        result = await self._session.execute(
            sa.select(UserModel).where(UserModel.email == email)
        )
        row = result.scalars().one_or_none()
        return self._to_credentials(row) if row else None

    async def get_credentials_by_id(self, id_: uuid.UUID) -> Credentials | None:
        """Obtém as credenciais de um usuário pelo id. `None` se não encontrado."""
        result = await self._session.execute(
            sa.select(UserModel).where(UserModel.id == id_)
        )
        row = result.scalars().one_or_none()
        return self._to_credentials(row) if row else None

    def _to_credentials(self, row: UserModel) -> Credentials:
        return Credentials(
            id=row.id,
            password_hash=row.password_hash,
            is_active=row.is_active,
        )

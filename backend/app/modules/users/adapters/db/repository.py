import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.modules.users.adapters.db.models import User as UserModel
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import User


class UsersRepository(BaseRepository[UserModel, User, UserFilters]):
    model = UserModel
    filters_type = UserFilters

    async def get_by_email_or_none(self, email: str) -> User | None:
        """
        Obtém um usuário pelo seu email. Retorna `None` se o usuário não for encontrado.

        Args:
            email (str):
                Email do usuário a ser buscado.

        Returns:
            User | None:
                O usuário encontrado ou `None` se não for encontrado.
        """

        result = await self._session.execute(
            sa.select(self.model).where(self.model.email == email)
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User:
        """
        Obtém um usuário pelo seu email. Lança `NotFoundError` se o usuário não for
        encontrado.

        Args:
            email (str):
                Email do usuário a ser buscado.

        Returns:
            User:
                O usuário encontrado.

        Raises:
            NotFoundError:
                Se nenhum usuário for encontrado com o email fornecido.
        """

        user = await self.get_by_email_or_none(email)
        if user is None:
            raise NotFoundError(f"Usuário com email '{email}' não encontrado.")
        return user

    def _to_entity(self, row: UserModel) -> User:
        return User(
            id=row.id,
            email=row.email,
            name=row.name,
            phone=row.phone,
            is_active=row.is_active,
            updated_at=row.updated_at,
            created_at=row.created_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: UserFilters) -> sa.Select:
        if filters.q:
            stmt = stmt.where(UserModel.email.ilike(f"%{filters.q}%"))
        if filters.is_active is not None:
            stmt = stmt.where(UserModel.is_active == filters.is_active)
        return stmt

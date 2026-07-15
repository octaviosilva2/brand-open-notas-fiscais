from typing import Protocol

from app.core.db.ports import BaseRepositoryProtocol
from app.modules.users.application.dtos.filters import UserFilters
from app.modules.users.domain.entities import NewUser, UpdateUser, User


class UsersRepositoryProtocol(
    BaseRepositoryProtocol[User, UserFilters, NewUser, UpdateUser],
    Protocol,
):
    async def get_by_email_or_none(self, email: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User: ...

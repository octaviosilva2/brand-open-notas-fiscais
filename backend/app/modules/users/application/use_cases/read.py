import uuid

from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import User


class UsersReader:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um leitor de usuários

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def get_by_id(
        self,
        id: uuid.UUID,
    ) -> User:
        """
        Obtém um usuário pelo seu id.

        Args:
            id (uuid.UUID):
                UUID do usuário.
        """

        async with self._uow as uow:
            return await uow.users.get_by_id(id)

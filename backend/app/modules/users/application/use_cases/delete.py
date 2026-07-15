import uuid

from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol


class UsersDeleter:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um removedor de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def delete(
        self,
        id_: uuid.UUID,
    ) -> None:
        """
        Deleta um usuário.

        Args:
            id_ (uuid.UUID):
                UUID do usuário.
        """

        async with self._uow as uow:
            await uow.users.delete(id_)

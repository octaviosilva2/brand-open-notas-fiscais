import uuid

from app.core.actors.user import UserActor
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import UpdateUser, User


class UsersActivator:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um ativador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def activate(self, id: uuid.UUID, actor: UserActor) -> User:
        """
        Ativa um usuário.

        Args:
            id (uuid.UUID):
                UUID do usuário.
            actor (UserActor):
                Usuário que está executando a ação.
        """

        return await self._set_active_status(
            id_=id,
            is_active=True,
        )

    async def deactivate(self, id: uuid.UUID, actor: UserActor) -> User:
        """
        Inativa um usuário.

        Args:
            id (uuid.UUID):
                UUID do usuário.
            actor (UserActor):
                Usuário que está executando a ação.
        """

        return await self._set_active_status(
            id_=id,
            is_active=False,
        )

    async def _set_active_status(
        self,
        id_: uuid.UUID,
        is_active: bool,
    ) -> User:
        """
        Define o status de atividade de um usuário.

        Args:
            id_ (uuid.UUID):
                UUID do usuário.
            is_active (bool):
                Novo status de atividade do usuário.
        """

        async with self._uow as uow:
            return await uow.users.update(
                id_=id_,
                update_command=UpdateUser(is_active=is_active),
            )

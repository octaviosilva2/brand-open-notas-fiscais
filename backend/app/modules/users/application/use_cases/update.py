import uuid

from app.core.security.passwords import hash_password
from app.modules.users.application.dtos.commands import UpdateUserCommand
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import UpdateUser, User


class UsersUpdater:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um atualizador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def update(
        self,
        id_: uuid.UUID,
        data: UpdateUserCommand,
    ) -> User:
        """
        Atualiza um usuário.

        Args:
            id_ (uuid.UUID):
                UUID do usuário.
            data (UpdateUserCommand):
                Dados a serem atualizados no usuário.
        """

        update_command = self._build_update_command(data)
        async with self._uow as uow:
            return await uow.users.update(
                id_=id_,
                update_command=update_command,
            )

    def _build_update_command(self, data: UpdateUserCommand) -> UpdateUser:
        """
        Converte o comando de aplicação em um comando de domínio.

        Descarta o `id` (informado separadamente) e converte a senha em texto
        plano para seu hash, mapeando `password` -> `password_hash`.
        """

        values = data.defined_values()

        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))

        return UpdateUser(**values)

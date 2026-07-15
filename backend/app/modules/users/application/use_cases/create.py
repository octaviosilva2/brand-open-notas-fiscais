from app.core.exceptions import ConflictError
from app.core.security.passwords import hash_password
from app.modules.users.application.dtos.commands import CreateUserCommand
from app.modules.users.application.ports.unit_of_work import UsersUnitOfWorkProtocol
from app.modules.users.domain.entities import NewUser, User


class UsersCreator:
    def __init__(self, uow: UsersUnitOfWorkProtocol) -> None:
        """
        Inicializa um criador de usuários.

        Args:
            uow (UsersUnitOfWorkProtocol):
                Unit of work de usuários.
        """

        self._uow = uow

    async def create(self, data: CreateUserCommand) -> User:
        """
        Cria um usuário.

        Args:
            data (CreateUserCommand):
                Dados do usuário a ser criado.
        """

        new_user = self._build_new_user(data)
        async with self._uow as uow:
            existing = await uow.users.get_by_email_or_none(data.email)
            if existing:
                raise ConflictError(f"Usuário com email '{data.email}' já existe.")
            return await uow.users.create(create_command=new_user)

    def _build_new_user(self, data: CreateUserCommand) -> NewUser:
        """
        Converte o comando de aplicação em um comando de domínio.

        Converte a senha em texto plano para seu hash, mapeando `password` ->
        `password_hash`, e define o usuário como ativo por padrão.
        """

        return NewUser(
            email=data.email,
            name=data.name,
            phone=data.phone,
            password_hash=hash_password(data.password),
            is_active=True,
        )

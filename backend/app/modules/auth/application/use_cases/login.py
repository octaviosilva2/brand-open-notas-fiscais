from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
)
from app.core.security.passwords import verify_password
from app.modules.auth.application.dtos.commands import LoginCommand
from app.modules.auth.application.dtos.results import TokenPair
from app.modules.auth.application.ports.unit_of_work import AuthUnitOfWorkProtocol


class AuthLogin:
    def __init__(self, uow: AuthUnitOfWorkProtocol) -> None:
        """
        Inicializa o use case de login.

        Args:
            uow (AuthUnitOfWorkProtocol):
                Unit of work de autenticação.
        """

        self._uow = uow

    async def login(self, command: LoginCommand) -> TokenPair:
        """
        Autentica um usuário pelas credenciais e emite um par de tokens.

        Args:
            command (LoginCommand):
                Email e senha informados.

        Raises:
            UnauthorizedError:
                Se as credenciais forem inválidas ou o usuário estiver inativo.
        """

        async with self._uow as uow:
            credentials = await uow.credentials.get_credentials_by_email(command.email)

        if credentials is None or not verify_password(
            command.password, credentials.password_hash
        ):
            raise UnauthorizedError("Credenciais inválidas.")
        if not credentials.is_active:
            raise UnauthorizedError("Usuário inativo.")

        identity = TokenIdentity(subject=credentials.id)
        return TokenPair(
            access_token=create_access_token(identity),
            refresh_token=create_refresh_token(identity),
        )

import uuid

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.modules.auth.application.dtos.commands import RefreshCommand
from app.modules.auth.application.dtos.results import TokenPair
from app.modules.auth.application.ports.unit_of_work import AuthUnitOfWorkProtocol


class AuthRefresher:
    def __init__(self, uow: AuthUnitOfWorkProtocol) -> None:
        """
        Inicializa o use case de renovação de tokens.

        Args:
            uow (AuthUnitOfWorkProtocol):
                Unit of work de autenticação.
        """

        self._uow = uow

    async def refresh(self, command: RefreshCommand) -> TokenPair:
        """
        Renova o par de tokens a partir de um refresh token válido, revalidando o
        usuário no banco.

        Args:
            command (RefreshCommand):
                Refresh token informado.

        Raises:
            UnauthorizedError:
                Se o token for inválido/expirado ou o usuário não existir ou estiver
                inativo.
        """

        claims = decode_refresh_token(command.refresh_token)
        user_id = uuid.UUID(claims["sub"])

        async with self._uow as uow:
            credentials = await uow.credentials.get_credentials_by_id(user_id)

        if credentials is None or not credentials.is_active:
            raise UnauthorizedError("Usuário inválido ou inativo.")

        identity = TokenIdentity(subject=credentials.id)
        return TokenPair(
            access_token=create_access_token(identity),
            refresh_token=create_refresh_token(identity),
        )

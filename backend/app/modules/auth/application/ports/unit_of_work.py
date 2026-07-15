from types import TracebackType
from typing import Protocol, Self

from app.modules.auth.application.ports.repositories import AuthRepositoryProtocol


class AuthUnitOfWorkProtocol(Protocol):
    @property
    def credentials(self) -> AuthRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

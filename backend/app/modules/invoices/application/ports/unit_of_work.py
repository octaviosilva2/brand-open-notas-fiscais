# app/modules/invoices/application/ports/unit_of_work.py
from types import TracebackType
from typing import Protocol, Self

from app.modules.invoices.application.ports.repository import InvoicesRepositoryProtocol


class InvoicesUnitOfWorkProtocol(Protocol):
    @property
    def invoices(self) -> InvoicesRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

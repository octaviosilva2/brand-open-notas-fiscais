# app/modules/recurrences/application/ports/unit_of_work.py
from types import TracebackType
from typing import Protocol, Self

from app.modules.recurrences.application.ports.repository import (
    RecurrencesRepositoryProtocol,
)


class RecurrencesUnitOfWorkProtocol(Protocol):
    @property
    def recurrences(self) -> RecurrencesRepositoryProtocol: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...

# app/modules/recurrences/adapters/db/unit_of_work.py
from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.unit_of_work import BaseUnitOfWork
from app.modules.recurrences.adapters.db.repository import RecurrencesRepository


class RecurrencesUnitOfWork(BaseUnitOfWork):
    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        super().__init__(session_factory=session_factory)
        self._recurrences: RecurrencesRepository | None = None

    @property
    def recurrences(self) -> RecurrencesRepository:
        if self._recurrences is None:
            raise RuntimeError("Repositório de recorrências não inicializado.")
        return self._recurrences

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self._recurrences = RecurrencesRepository(self.session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._recurrences = None

# app/modules/recurrences/application/use_cases/recurrences_reader.py
import uuid

from app.modules.recurrences.application.ports.unit_of_work import (
    RecurrencesUnitOfWorkProtocol,
)
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesReader:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(self, id_: uuid.UUID) -> Recurrence:
        async with self._uow as uow:
            return await uow.recurrences.get_by_id(id_)

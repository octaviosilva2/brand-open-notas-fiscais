# app/modules/recurrences/application/ports/repository.py
import uuid
from datetime import date
from typing import Protocol

from app.modules.recurrences.domain.entities import (
    NewRecurrence,
    Recurrence,
    UpdateRecurrence,
)


class RecurrencesRepositoryProtocol(Protocol):
    async def get_by_id(self, id_: uuid.UUID) -> Recurrence: ...
    async def get_by_id_or_none(self, id_: uuid.UUID) -> Recurrence | None: ...
    async def create(self, create_command: NewRecurrence) -> Recurrence: ...
    async def update(
        self, id_: uuid.UUID, update_command: UpdateRecurrence
    ) -> Recurrence: ...
    async def get_active_due_in_range(
        self, from_date: date, to_date: date
    ) -> list[Recurrence]: ...

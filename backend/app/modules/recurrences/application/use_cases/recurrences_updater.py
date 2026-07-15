# app/modules/recurrences/application/use_cases/recurrences_updater.py
import uuid

from app.core.exceptions import NotFoundError
from app.core.types import is_unset
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.recurrences.application.dtos.commands import UpdateRecurrenceCommand
from app.modules.recurrences.application.ports.unit_of_work import (
    RecurrencesUnitOfWorkProtocol,
)
from app.modules.recurrences.domain.entities import Recurrence, UpdateRecurrence


class RecurrencesUpdater:
    def __init__(
        self,
        uow: RecurrencesUnitOfWorkProtocol,
        clients_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def update(self, id_: uuid.UUID, data: UpdateRecurrenceCommand) -> Recurrence:
        if not is_unset(data.client_id):
            clients_uow = self._clients_uow_factory()
            async with clients_uow as cuow:
                client = await cuow.clients.get_by_id_or_none(data.client_id)  # type: ignore[arg-type]
            if client is None:
                raise NotFoundError(
                    f"Cliente com ID '{data.client_id}' não encontrado."
                )

        async with self._uow as uow:
            return await uow.recurrences.update(
                id_,
                UpdateRecurrence(**data.defined_values()),
            )

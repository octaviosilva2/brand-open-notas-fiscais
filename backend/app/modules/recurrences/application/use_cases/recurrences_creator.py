# app/modules/recurrences/application/use_cases/recurrences_creator.py

from app.core.exceptions import NotFoundError
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.recurrences.application.dtos.commands import CreateRecurrenceCommand
from app.modules.recurrences.application.ports.unit_of_work import (
    RecurrencesUnitOfWorkProtocol,
)
from app.modules.recurrences.domain.entities import NewRecurrence, Recurrence


class RecurrencesCreator:
    def __init__(
        self,
        uow: RecurrencesUnitOfWorkProtocol,
        clients_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def create(self, data: CreateRecurrenceCommand) -> Recurrence:
        clients_uow = self._clients_uow_factory()
        async with clients_uow as cuow:
            client = await cuow.clients.get_by_id_or_none(data.client_id)
        if client is None:
            raise NotFoundError(f"Cliente com ID '{data.client_id}' não encontrado.")

        async with self._uow as uow:
            return await uow.recurrences.create(
                NewRecurrence(
                    client_id=data.client_id,
                    description=data.description,
                    amount=data.amount,
                    day_of_month=data.day_of_month,
                    start_date=data.start_date,
                    end_date=data.end_date,
                    is_active=data.is_active,
                    inf_dps=data.inf_dps,
                )
            )

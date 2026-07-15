# app/modules/clients/application/use_cases/clients_updater.py
import uuid

from app.core.exceptions import ConflictError
from app.core.types import is_unset
from app.modules.clients.application.dtos.commands import UpdateClientCommand
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client, UpdateClient


class ClientsUpdater:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def update(self, id_: uuid.UUID, data: UpdateClientCommand) -> Client:
        async with self._uow as uow:
            if not is_unset(data.document):
                existing = await uow.clients.get_by_document_or_none(data.document)  # type: ignore[arg-type]
                if existing and existing.id != id_:
                    raise ConflictError(
                        f"Documento '{data.document}' já pertence a outro cliente."
                    )
            return await uow.clients.update(
                id_,
                UpdateClient(**data.defined_values()),
            )

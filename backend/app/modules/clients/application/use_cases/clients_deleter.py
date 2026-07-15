# app/modules/clients/application/use_cases/clients_deleter.py
import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol


class ClientsDeleter:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def delete(self, id_: uuid.UUID) -> None:
        try:
            async with self._uow as uow:
                await uow.clients.delete(id_)
        except IntegrityError as err:
            raise ConflictError(
                "Cliente possui recorrências vinculadas e não pode ser excluído."
            ) from err

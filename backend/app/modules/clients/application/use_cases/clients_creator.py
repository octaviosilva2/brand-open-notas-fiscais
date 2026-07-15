# app/modules/clients/application/use_cases/clients_creator.py
from app.core.exceptions import ConflictError
from app.modules.clients.application.dtos.commands import CreateClientCommand
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client, NewClient


class ClientsCreator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def create(self, data: CreateClientCommand) -> Client:
        async with self._uow as uow:
            existing = await uow.clients.get_by_document_or_none(data.document)
            if existing:
                raise ConflictError(
                    f"Cliente com documento '{data.document}' já existe."
                )
            return await uow.clients.create(
                NewClient(
                    document=data.document,
                    name=data.name,
                    municipal_registration=data.municipal_registration,
                    phone=data.phone,
                    email=data.email,
                    zip_code=data.zip_code,
                    street=data.street,
                    number=data.number,
                    complement=data.complement,
                    neighborhood=data.neighborhood,
                    ibge_city_code=data.ibge_city_code,
                    is_active=data.is_active,
                )
            )

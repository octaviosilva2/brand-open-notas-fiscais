# app/modules/clients/application/use_cases/clients_paginator.py
from app.core.pagination.params import Page, PageParams
from app.modules.clients.application.dtos.filters import ClientFilters
from app.modules.clients.application.ports.unit_of_work import ClientsUnitOfWorkProtocol
from app.modules.clients.domain.entities import Client


class ClientsPaginator:
    def __init__(self, uow: ClientsUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: ClientFilters | None = None,
    ) -> Page[Client]:
        async with self._uow as uow:
            return await uow.clients.paginate(
                page_params=page_params,
                filters=filters,
            )

# app/modules/clients/adapters/http/router.py
import uuid

from fastapi import APIRouter, Depends

from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.clients.adapters.http.dependencies import (
    ClientsUnitOfWorkDep,
    PaginationFiltersDep,
)
from app.modules.clients.adapters.http.schemas import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
)
from app.modules.clients.application.dtos.commands import (
    CreateClientCommand,
    UpdateClientCommand,
)
from app.modules.clients.application.use_cases.clients_creator import ClientsCreator
from app.modules.clients.application.use_cases.clients_deleter import ClientsDeleter
from app.modules.clients.application.use_cases.clients_paginator import ClientsPaginator
from app.modules.clients.application.use_cases.clients_reader import ClientsReader
from app.modules.clients.application.use_cases.clients_updater import ClientsUpdater
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("", response_model=PaginatedResponse[ClientRead])
async def list_clients(
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: ClientsUnitOfWorkDep,
) -> PaginatedResponse[ClientRead]:
    paginator = ClientsPaginator(uow=uow)
    page = await paginator.paginate(page_params=page_params, filters=filters)
    return build_paginated_response(
        items=[ClientRead.model_validate(c.to_dict()) for c in page.items],
        total=page.total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.post("", response_model=ClientRead, status_code=201)
async def create_client(
    data: ClientCreate,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    creator = ClientsCreator(uow=uow)
    client = await creator.create(
        CreateClientCommand(**data.model_dump(exclude_unset=True))
    )
    return ClientRead.model_validate(client.to_dict())


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    reader = ClientsReader(uow=uow)
    client = await reader.get_by_id(client_id)
    return ClientRead.model_validate(client.to_dict())


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: uuid.UUID,
    data: ClientUpdate,
    uow: ClientsUnitOfWorkDep,
) -> ClientRead:
    updater = ClientsUpdater(uow=uow)
    client = await updater.update(
        client_id,
        UpdateClientCommand(**data.model_dump(exclude_unset=True)),
    )
    return ClientRead.model_validate(client.to_dict())


@router.delete("/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    uow: ClientsUnitOfWorkDep,
) -> None:
    deleter = ClientsDeleter(uow=uow)
    await deleter.delete(client_id)

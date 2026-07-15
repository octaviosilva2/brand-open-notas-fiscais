# app/modules/clients/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.clients.adapters.db.factories import make_unit_of_work
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork
from app.modules.clients.adapters.http.schemas import ClientsPaginationFilters
from app.modules.clients.application.dtos.filters import ClientFilters

ClientsUnitOfWorkDep = Annotated[ClientsUnitOfWork, Depends(make_unit_of_work)]


def get_pagination_filters(
    query_params: Annotated[ClientsPaginationFilters, Depends()],
) -> ClientFilters:
    return ClientFilters(search=query_params.search)


PaginationFiltersDep = Annotated[ClientFilters, Depends(get_pagination_filters)]

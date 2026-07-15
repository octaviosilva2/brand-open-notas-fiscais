# app/modules/recurrences/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.clients.adapters.db.unit_of_work import ClientsUnitOfWork
from app.modules.recurrences.adapters.db.factories import make_unit_of_work
from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork
from app.modules.recurrences.adapters.http.schemas import RecurrencesPaginationFilters
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters

RecurrencesUnitOfWorkDep = Annotated[RecurrencesUnitOfWork, Depends(make_unit_of_work)]
ClientsUnitOfWorkDep = Annotated[ClientsUnitOfWork, Depends(make_clients_uow)]


def get_pagination_filters(
    query_params: Annotated[RecurrencesPaginationFilters, Depends()],
) -> RecurrenceFilters:
    return RecurrenceFilters(
        client_id=query_params.client_id,
        is_active=query_params.is_active,
    )


PaginationFiltersDep = Annotated[RecurrenceFilters, Depends(get_pagination_filters)]

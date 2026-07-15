# app/modules/recurrences/application/use_cases/recurrences_paginator.py
from app.core.pagination.params import Page, PageParams
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters
from app.modules.recurrences.application.ports.unit_of_work import (
    RecurrencesUnitOfWorkProtocol,
)
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesPaginator:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def paginate(
        self,
        page_params: PageParams,
        filters: RecurrenceFilters | None = None,
    ) -> Page[Recurrence]:
        async with self._uow as uow:
            return await uow.recurrences.paginate(
                page_params=page_params,
                filters=filters,
            )

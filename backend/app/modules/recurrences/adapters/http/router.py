# app/modules/recurrences/adapters/http/router.py
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import ValidationAppError
from app.core.pagination.dependencies import PageParamsDep
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.recurrences.adapters.http.dependencies import (
    ClientsUnitOfWorkDep,
    PaginationFiltersDep,
    RecurrencesUnitOfWorkDep,
)
from app.modules.recurrences.adapters.http.schemas import (
    RecurrenceCreate,
    RecurrenceRead,
    RecurrenceUpdate,
    UpcomingItemRead,
)
from app.modules.recurrences.application.dtos.commands import (
    CreateRecurrenceCommand,
    UpdateRecurrenceCommand,
)
from app.modules.recurrences.application.use_cases.recurrences_creator import (
    RecurrencesCreator,
)
from app.modules.recurrences.application.use_cases.recurrences_paginator import (
    RecurrencesPaginator,
)
from app.modules.recurrences.application.use_cases.recurrences_reader import (
    RecurrencesReader,
)
from app.modules.recurrences.application.use_cases.recurrences_updater import (
    RecurrencesUpdater,
)
from app.modules.recurrences.application.use_cases.upcoming_reader import UpcomingReader
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("/upcoming", response_model=list[UpcomingItemRead])
async def get_upcoming(
    uow: RecurrencesUnitOfWorkDep,
    from_date: date = Query(..., alias="from"),  # noqa: B008
    to_date: date = Query(..., alias="to"),  # noqa: B008
) -> list[UpcomingItemRead]:
    if (to_date - from_date).days > 90:
        raise ValidationAppError("Intervalo máximo é de 90 dias.")
    reader = UpcomingReader(uow=uow)
    items = await reader.list_upcoming(from_date, to_date)
    return [UpcomingItemRead(**vars(item)) for item in items]


@router.get("", response_model=PaginatedResponse[RecurrenceRead])
async def list_recurrences(
    filters: PaginationFiltersDep,
    page_params: PageParamsDep,
    uow: RecurrencesUnitOfWorkDep,
) -> PaginatedResponse[RecurrenceRead]:
    paginator = RecurrencesPaginator(uow=uow)
    page = await paginator.paginate(page_params=page_params, filters=filters)
    return build_paginated_response(
        items=[RecurrenceRead.model_validate(r.to_dict()) for r in page.items],
        total=page.total,
        page=page_params.page,
        page_size=page_params.page_size,
    )


@router.post("", response_model=RecurrenceRead, status_code=201)
async def create_recurrence(
    data: RecurrenceCreate,
    uow: RecurrencesUnitOfWorkDep,
    clients_uow: ClientsUnitOfWorkDep,
) -> RecurrenceRead:
    creator = RecurrencesCreator(uow=uow, clients_uow_factory=lambda: clients_uow)
    payload = data.model_dump(exclude_unset=True)
    payload["inf_dps"] = data.inf_dps.model_dump(exclude_none=True)
    rec = await creator.create(CreateRecurrenceCommand(**payload))
    return RecurrenceRead.model_validate(rec.to_dict())


@router.get("/{recurrence_id}", response_model=RecurrenceRead)
async def get_recurrence(
    recurrence_id: uuid.UUID,
    uow: RecurrencesUnitOfWorkDep,
) -> RecurrenceRead:
    reader = RecurrencesReader(uow=uow)
    rec = await reader.get_by_id(recurrence_id)
    return RecurrenceRead.model_validate(rec.to_dict())


@router.patch("/{recurrence_id}", response_model=RecurrenceRead)
async def update_recurrence(
    recurrence_id: uuid.UUID,
    data: RecurrenceUpdate,
    uow: RecurrencesUnitOfWorkDep,
    clients_uow: ClientsUnitOfWorkDep,
) -> RecurrenceRead:
    updater = RecurrencesUpdater(uow=uow, clients_uow_factory=lambda: clients_uow)
    payload = data.model_dump(exclude_unset=True)
    if "inf_dps" in payload and data.inf_dps is not None:
        payload["inf_dps"] = data.inf_dps.model_dump(exclude_none=True)
    rec = await updater.update(
        recurrence_id,
        UpdateRecurrenceCommand(**payload),
    )
    return RecurrenceRead.model_validate(rec.to_dict())

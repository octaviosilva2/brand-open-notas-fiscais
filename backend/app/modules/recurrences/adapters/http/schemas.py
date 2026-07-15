# app/modules/recurrences/adapters/http/schemas.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

from app.modules.recurrences.domain.inf_dps import InfDps


class RecurrenceCreate(BaseModel):
    client_id: uuid.UUID
    description: Annotated[str, Field(max_length=1000, min_length=1)]
    amount: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    day_of_month: Annotated[int, Field(ge=1, le=31)]
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    inf_dps: InfDps

    @model_validator(mode="after")
    def validate_end_date(self) -> RecurrenceCreate:
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date deve ser maior ou igual a start_date.")
        return self


class RecurrenceUpdate(BaseModel):
    client_id: uuid.UUID | None = None
    description: Annotated[str | None, Field(max_length=1000, min_length=1)] = None
    amount: Annotated[Decimal | None, Field(gt=0, decimal_places=2)] = None
    day_of_month: Annotated[int | None, Field(ge=1, le=31)] = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    inf_dps: InfDps | None = None


class RecurrenceRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool
    inf_dps: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpcomingItemRead(BaseModel):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    amount: Decimal
    description: str
    scheduled_date: date


class RecurrencesPaginationFilters(BaseModel):
    client_id: uuid.UUID | None = None
    is_active: bool | None = None

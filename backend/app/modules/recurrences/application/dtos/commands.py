# app/modules/recurrences/application/dtos/commands.py
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateRecurrenceCommand(BaseCreateCommand):
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None = None
    is_active: bool = True
    inf_dps: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class UpdateRecurrenceCommand(BaseUpdateCommand):
    client_id: uuid.UUID | Unset = UNSET
    description: str | Unset = UNSET
    amount: Decimal | Unset = UNSET
    day_of_month: int | Unset = UNSET
    start_date: date | Unset = UNSET
    end_date: date | None | Unset = UNSET
    is_active: bool | Unset = UNSET
    inf_dps: dict[str, Any] | Unset = UNSET

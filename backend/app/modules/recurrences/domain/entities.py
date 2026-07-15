# app/modules/recurrences/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewRecurrence(BaseCreateCommand):
    client_id: uuid.UUID
    description: str
    amount: Decimal
    day_of_month: int
    start_date: date
    end_date: date | None
    is_active: bool
    inf_dps: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UpdateRecurrence(BaseUpdateCommand):
    client_id: uuid.UUID | Unset = UNSET
    description: str | Unset = UNSET
    amount: Decimal | Unset = UNSET
    day_of_month: int | Unset = UNSET
    start_date: date | Unset = UNSET
    end_date: date | None | Unset = UNSET
    is_active: bool | Unset = UNSET
    inf_dps: dict[str, Any] | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Recurrence:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "description": self.description,
            "amount": self.amount,
            "day_of_month": self.day_of_month,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_active": self.is_active,
            "inf_dps": self.inf_dps,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

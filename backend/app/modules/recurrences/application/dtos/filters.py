# app/modules/recurrences/application/dtos/filters.py
import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecurrenceFilters:
    client_id: uuid.UUID | None = None
    is_active: bool | None = None

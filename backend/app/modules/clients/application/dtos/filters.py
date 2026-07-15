# app/modules/clients/application/dtos/filters.py
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClientFilters:
    search: str | None = None

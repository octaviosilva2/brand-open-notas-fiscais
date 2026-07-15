# app/modules/invoices/application/dtos/filters.py
import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class InvoiceFilters:
    status: str | None = None
    client_id: uuid.UUID | None = None
    from_date: date | None = None
    to_date: date | None = None

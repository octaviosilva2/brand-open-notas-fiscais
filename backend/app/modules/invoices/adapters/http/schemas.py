# app/modules/invoices/adapters/http/schemas.py
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class InvoiceRead(BaseModel):
    """Schema de leitura de uma invoice (listagem e operações gerais)."""

    id: uuid.UUID
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    client_name: str
    scheduled_date: date
    amount: Decimal
    description: str
    status: Literal["pending", "processing", "success", "error"]
    n_dps: int | None
    protocol: str | None
    nf_number: str | None
    pdf_url: str | None
    error_message: str | None
    emission_date: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceDetailRead(InvoiceRead):
    """InvoiceRead com campos xml — usado apenas em GET /invoices/{id}."""

    xml_sent: str | None
    xml_response: str | None


class InvoicesPaginationFilters(BaseModel):
    """Filtros de paginação aceitos como query params na listagem de invoices."""

    status: str | None = None
    client_id: uuid.UUID | None = None
    from_date: date | None = Field(None, alias="from")
    to_date: date | None = Field(None, alias="to")

    model_config = {"populate_by_name": True}

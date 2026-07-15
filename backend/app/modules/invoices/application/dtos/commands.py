# app/modules/invoices/application/dtos/commands.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateInvoiceCommand(BaseCreateCommand):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: str = "pending"


@dataclass(frozen=True, slots=True)
class UpdateInvoiceCommand(BaseUpdateCommand):
    status: str | Unset = UNSET
    n_dps: int | None | Unset = UNSET
    protocol: str | None | Unset = UNSET
    nf_number: str | None | Unset = UNSET
    pdf_url: str | None | Unset = UNSET
    xml_sent: str | None | Unset = UNSET
    xml_response: str | None | Unset = UNSET
    error_message: str | None | Unset = UNSET
    emission_date: datetime | None | Unset = UNSET

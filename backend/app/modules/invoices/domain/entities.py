# app/modules/invoices/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset

InvoiceStatus = Literal["pending", "processing", "success", "error"]


@dataclass(frozen=True, slots=True)
class NewInvoice(BaseCreateCommand):
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: InvoiceStatus = "pending"
    n_dps: int | None = None
    protocol: str | None = None
    nf_number: str | None = None
    pdf_url: str | None = None
    xml_sent: str | None = None
    xml_response: str | None = None
    error_message: str | None = None
    emission_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class UpdateInvoice(BaseUpdateCommand):
    status: InvoiceStatus | Unset = UNSET
    n_dps: int | None | Unset = UNSET
    protocol: str | None | Unset = UNSET
    nf_number: str | None | Unset = UNSET
    pdf_url: str | None | Unset = UNSET
    xml_sent: str | None | Unset = UNSET
    xml_response: str | None | Unset = UNSET
    error_message: str | None | Unset = UNSET
    emission_date: datetime | None | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Invoice:
    id: uuid.UUID
    recurrence_id: uuid.UUID
    client_id: uuid.UUID
    scheduled_date: date
    amount: Decimal
    description: str
    status: InvoiceStatus
    n_dps: int | None
    protocol: str | None
    nf_number: str | None
    pdf_url: str | None
    xml_sent: str | None
    xml_response: str | None
    error_message: str | None
    emission_date: datetime | None
    created_at: datetime
    updated_at: datetime

    def to_dict(self, client_name: str = "") -> dict[str, Any]:
        return {
            "id": self.id,
            "recurrence_id": self.recurrence_id,
            "client_id": self.client_id,
            "client_name": client_name,
            "scheduled_date": self.scheduled_date,
            "amount": self.amount,
            "description": self.description,
            "status": self.status,
            "n_dps": self.n_dps,
            "protocol": self.protocol,
            "nf_number": self.nf_number,
            "pdf_url": self.pdf_url,
            "xml_sent": self.xml_sent,
            "xml_response": self.xml_response,
            "error_message": self.error_message,
            "emission_date": self.emission_date,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

# app/integrations/betha/models.py
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.modules.clients.domain.entities import Client
from app.modules.recurrences.domain.entities import Recurrence


@dataclass(frozen=True)
class DpsPayload:
    recurrence_id: uuid.UUID
    client: Client
    recurrence: Recurrence
    emission_date: date
    n_dps: int


@dataclass(frozen=True)
class PollResult:
    status: Literal["PROCESSADO", "ERRO", "AGUARDANDO"]
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None
    raw_response: str = ""


@dataclass(frozen=True)
class EmissionResult:
    ok: bool
    protocol: str | None = None
    nf_number: str | None = None
    pdf_url: str | None = None
    xml_sent: str = ""
    xml_response: str = ""
    error_message: str | None = None

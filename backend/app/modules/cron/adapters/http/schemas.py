# app/modules/cron/adapters/http/schemas.py
from datetime import date

from pydantic import BaseModel


class CronItemResultSchema(BaseModel):
    recurrence_id: str
    client_name: str
    invoice_id: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


class CronResultSchema(BaseModel):
    date: date
    total: int
    success: int
    error: int
    results: list[CronItemResultSchema]

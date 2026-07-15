# app/modules/lookups/schemas.py
from pydantic import BaseModel


class LookupOption(BaseModel):
    """Opção genérica de lookup: `value` é o código, `label` o texto exibível."""

    value: str
    label: str

# app/modules/clients/adapters/http/schemas.py
import re
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

_ADDRESS_FIELDS = ("zip_code", "street", "number", "neighborhood", "ibge_city_code")


def _validate_document(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14):
        raise ValueError("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    return digits


class ClientCreate(BaseModel):
    document: str
    name: Annotated[str, Field(max_length=150, min_length=1)]
    municipal_registration: Annotated[str | None, Field(max_length=15)] = None
    phone: Annotated[str | None, Field(max_length=20)] = None
    email: EmailStr | None = None
    zip_code: Annotated[str | None, Field(max_length=8, pattern=r"^\d{8}$")] = None
    street: Annotated[str | None, Field(max_length=255)] = None
    number: Annotated[str | None, Field(max_length=60)] = None
    complement: Annotated[str | None, Field(max_length=156)] = None
    neighborhood: Annotated[str | None, Field(max_length=60)] = None
    ibge_city_code: Annotated[str | None, Field(max_length=7, pattern=r"^\d{7}$")] = (
        None
    )

    @field_validator("document", mode="before")
    @classmethod
    def validate_document(cls, v: str) -> str:
        return _validate_document(v)

    @model_validator(mode="after")
    def validate_address_group(self) -> ClientCreate:
        has_any = any(getattr(self, f) is not None for f in _ADDRESS_FIELDS)
        if has_any:
            missing = [f for f in _ADDRESS_FIELDS if getattr(self, f) is None]
            if missing:
                raise ValueError(
                    f"Quando qualquer campo de endereço é informado, os campos "
                    f"{missing} também são obrigatórios."
                )
        return self


class ClientUpdate(BaseModel):
    document: str | None = None
    name: Annotated[str | None, Field(max_length=150, min_length=1)] = None
    municipal_registration: Annotated[str | None, Field(max_length=15)] = None
    phone: Annotated[str | None, Field(max_length=20)] = None
    email: EmailStr | None = None
    zip_code: Annotated[str | None, Field(max_length=8, pattern=r"^\d{8}$")] = None
    street: Annotated[str | None, Field(max_length=255)] = None
    number: Annotated[str | None, Field(max_length=60)] = None
    complement: Annotated[str | None, Field(max_length=156)] = None
    neighborhood: Annotated[str | None, Field(max_length=60)] = None
    ibge_city_code: Annotated[str | None, Field(max_length=7, pattern=r"^\d{7}$")] = (
        None
    )

    @field_validator("document", mode="before")
    @classmethod
    def validate_document(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_document(v)


class ClientRead(BaseModel):
    id: UUID
    document: str
    document_type: Literal["CPF", "CNPJ"]
    name: str
    municipal_registration: str | None
    phone: str | None
    email: str | None
    zip_code: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    ibge_city_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientsPaginationFilters(BaseModel):
    search: str | None = None

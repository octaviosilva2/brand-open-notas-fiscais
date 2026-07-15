# app/modules/clients/domain/entities.py
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewClient(BaseCreateCommand):
    document: str
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


@dataclass(frozen=True, slots=True)
class UpdateClient(BaseUpdateCommand):
    document: str | Unset = UNSET
    name: str | Unset = UNSET
    municipal_registration: str | None | Unset = UNSET
    phone: str | None | Unset = UNSET
    email: str | None | Unset = UNSET
    zip_code: str | None | Unset = UNSET
    street: str | None | Unset = UNSET
    number: str | None | Unset = UNSET
    complement: str | None | Unset = UNSET
    neighborhood: str | None | Unset = UNSET
    ibge_city_code: str | None | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class Client:
    id: uuid.UUID
    document: str
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

    @property
    def document_type(self) -> Literal["CPF", "CNPJ"]:
        return "CPF" if len(self.document) == 11 else "CNPJ"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document": self.document,
            "name": self.name,
            "municipal_registration": self.municipal_registration,
            "phone": self.phone,
            "email": self.email,
            "zip_code": self.zip_code,
            "street": self.street,
            "number": self.number,
            "complement": self.complement,
            "neighborhood": self.neighborhood,
            "ibge_city_code": self.ibge_city_code,
            "is_active": self.is_active,
            "document_type": self.document_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

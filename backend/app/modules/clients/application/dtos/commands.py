# app/modules/clients/application/dtos/commands.py
from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateClientCommand(BaseCreateCommand):
    document: str
    name: str
    municipal_registration: str | None = None
    phone: str | None = None
    email: str | None = None
    zip_code: str | None = None
    street: str | None = None
    number: str | None = None
    complement: str | None = None
    neighborhood: str | None = None
    ibge_city_code: str | None = None
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class UpdateClientCommand(BaseUpdateCommand):
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

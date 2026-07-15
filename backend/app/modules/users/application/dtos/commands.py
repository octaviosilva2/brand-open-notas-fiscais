from dataclasses import dataclass

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class CreateUserCommand(BaseCreateCommand):
    name: str
    email: str
    phone: str
    password: str


@dataclass(frozen=True, slots=True)
class UpdateUserCommand(BaseUpdateCommand):
    name: str | Unset = UNSET
    email: str | Unset = UNSET
    phone: str | Unset = UNSET
    password: str | Unset = UNSET
    is_active: bool | Unset = UNSET

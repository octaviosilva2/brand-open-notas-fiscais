import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.types import UNSET, BaseCreateCommand, BaseUpdateCommand, Unset


@dataclass(frozen=True, slots=True)
class NewUser(BaseCreateCommand):
    email: str
    name: str
    phone: str
    password_hash: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class UpdateUser(BaseUpdateCommand):
    email: str | Unset = UNSET
    name: str | Unset = UNSET
    password_hash: str | Unset = UNSET
    is_active: bool | Unset = UNSET


@dataclass(frozen=True, slots=True)
class User:
    id: uuid.UUID
    email: str
    name: str
    phone: str
    is_active: bool
    updated_at: datetime
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "is_active": self.is_active,
            "updated_at": self.updated_at,
            "created_at": self.created_at,
        }

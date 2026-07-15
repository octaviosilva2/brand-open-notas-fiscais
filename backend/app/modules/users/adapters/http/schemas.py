from datetime import datetime
from typing import Annotated

from pydantic import UUID7, BaseModel, EmailStr, Field

Name = Annotated[str, Field(max_length=255)]
Phone = Annotated[str, Field(max_length=20)]
Password = Annotated[str, Field(min_length=8)]


class UserBase(BaseModel):
    name: Name
    email: EmailStr
    phone: Phone


class UserCreate(UserBase):
    password: Password


class UserRead(UserBase):
    id: UUID7
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    name: Name | None = None
    email: EmailStr | None = None
    phone: Phone | None = None


class ChangePassword(BaseModel):
    current_password: Password
    password: Password


class UsersPaginationFilters(BaseModel):
    q: str | None = None
    is_active: bool | None = None

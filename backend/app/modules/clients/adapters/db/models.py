# app/modules/clients/adapters/db/models.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    document: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    municipal_registration: Mapped[str | None] = mapped_column(
        String(15), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(80), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    number: Mapped[str | None] = mapped_column(String(60), nullable=True)
    complement: Mapped[str | None] = mapped_column(String(156), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(60), nullable=True)
    ibge_city_code: Mapped[str | None] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_clients_document", "document", unique=True),
        Index("ix_clients_name", "name"),
    )

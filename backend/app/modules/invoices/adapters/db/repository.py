# app/modules/invoices/adapters/db/repository.py
import uuid
from datetime import date

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.core.exceptions import NotFoundError
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.invoices.adapters.db.models import Invoice as InvoiceModel
from app.modules.invoices.application.dtos.filters import InvoiceFilters
from app.modules.invoices.domain.entities import Invoice


class InvoicesRepository(BaseRepository[InvoiceModel, Invoice, InvoiceFilters]):
    model = InvoiceModel
    filters_type = InvoiceFilters

    def _to_entity(self, row: InvoiceModel) -> Invoice:
        return Invoice(
            id=row.id,
            recurrence_id=row.recurrence_id,
            client_id=row.client_id,
            scheduled_date=row.scheduled_date,
            amount=row.amount,
            description=row.description,
            status=row.status,
            n_dps=row.n_dps,
            protocol=row.protocol,
            nf_number=row.nf_number,
            pdf_url=row.pdf_url,
            xml_sent=row.xml_sent,
            xml_response=row.xml_response,
            error_message=row.error_message,
            emission_date=row.emission_date,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: InvoiceFilters) -> sa.Select:
        if filters.status:
            stmt = stmt.where(InvoiceModel.status == filters.status)
        if filters.client_id:
            stmt = stmt.where(InvoiceModel.client_id == filters.client_id)
        if filters.from_date:
            stmt = stmt.where(InvoiceModel.scheduled_date >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(InvoiceModel.scheduled_date <= filters.to_date)
        return stmt.order_by(
            InvoiceModel.scheduled_date.desc(), InvoiceModel.created_at.desc()
        )

    async def get_with_client_name(self, id_: uuid.UUID) -> tuple[Invoice, str]:
        stmt = (
            sa.select(InvoiceModel, ClientModel.name)
            .join(ClientModel, InvoiceModel.client_id == ClientModel.id)
            .where(InvoiceModel.id == id_)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(f"Invoice com ID {id_} não encontrado.")
        return self._to_entity(row[0]), row[1]

    async def get_by_recurrence_and_date(
        self, recurrence_id: uuid.UUID, scheduled_date: date
    ) -> Invoice | None:
        result = await self._session.execute(
            sa.select(InvoiceModel).where(
                InvoiceModel.recurrence_id == recurrence_id,
                InvoiceModel.scheduled_date == scheduled_date,
            )
        )
        row = result.scalars().one_or_none()
        return self._to_entity(row) if row else None

    async def paginate_with_client_name(
        self, filters: InvoiceFilters, page: int, page_size: int
    ) -> tuple[list[tuple[Invoice, str]], int]:
        stmt = sa.select(InvoiceModel, ClientModel.name).join(
            ClientModel, InvoiceModel.client_id == ClientModel.id
        )
        if filters.status:
            stmt = stmt.where(InvoiceModel.status == filters.status)
        if filters.client_id:
            stmt = stmt.where(InvoiceModel.client_id == filters.client_id)
        if filters.from_date:
            stmt = stmt.where(InvoiceModel.scheduled_date >= filters.from_date)
        if filters.to_date:
            stmt = stmt.where(InvoiceModel.scheduled_date <= filters.to_date)

        stmt = stmt.order_by(
            InvoiceModel.scheduled_date.desc(), InvoiceModel.created_at.desc()
        )

        count_stmt = sa.select(sa.func.count()).select_from(stmt.subquery())
        total = await self._session.scalar(count_stmt) or 0

        result = await self._session.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )
        rows = result.all()
        return [(self._to_entity(r[0]), r[1]) for r in rows], total

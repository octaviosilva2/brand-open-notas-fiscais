# app/modules/recurrences/adapters/db/repository.py
from datetime import date

import sqlalchemy as sa

from app.core.db.repository import BaseRepository
from app.modules.clients.adapters.db.models import Client as ClientModel
from app.modules.recurrences.adapters.db.models import Recurrence as RecurrenceModel
from app.modules.recurrences.application.dtos.filters import RecurrenceFilters
from app.modules.recurrences.domain.entities import Recurrence


class RecurrencesRepository(
    BaseRepository[RecurrenceModel, Recurrence, RecurrenceFilters]
):
    model = RecurrenceModel
    filters_type = RecurrenceFilters

    def _to_entity(self, row: RecurrenceModel) -> Recurrence:
        return Recurrence(
            id=row.id,
            client_id=row.client_id,
            description=row.description,
            amount=row.amount,
            day_of_month=row.day_of_month,
            start_date=row.start_date,
            end_date=row.end_date,
            is_active=row.is_active,
            inf_dps=row.inf_dps,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def _apply_filters(self, stmt: sa.Select, filters: RecurrenceFilters) -> sa.Select:
        if filters.client_id is not None:
            stmt = stmt.where(RecurrenceModel.client_id == filters.client_id)
        if filters.is_active is not None:
            stmt = stmt.where(RecurrenceModel.is_active == filters.is_active)
        return stmt

    async def get_active_due_in_range(
        self, from_date: date, to_date: date
    ) -> list[tuple[Recurrence, str]]:
        """Retorna recorrências ativas com client_name, filtradas pelo intervalo."""
        stmt = (
            sa.select(RecurrenceModel, ClientModel.name)
            .join(ClientModel, RecurrenceModel.client_id == ClientModel.id)
            .where(RecurrenceModel.is_active == True)  # noqa: E712
            .where(RecurrenceModel.start_date <= to_date)
            .where(
                sa.or_(
                    RecurrenceModel.end_date.is_(None),
                    RecurrenceModel.end_date >= from_date,
                )
            )
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(self._to_entity(row[0]), row[1]) for row in rows]

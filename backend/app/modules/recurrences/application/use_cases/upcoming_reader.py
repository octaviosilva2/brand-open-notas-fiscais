# app/modules/recurrences/application/use_cases/upcoming_reader.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.modules.recurrences.application.ports.unit_of_work import (
    RecurrencesUnitOfWorkProtocol,
)
from app.modules.recurrences.domain.rules import resolve_emission_date


@dataclass(frozen=True)
class UpcomingItem:
    recurrence_id: UUID
    client_id: UUID
    client_name: str
    amount: Decimal
    description: str
    scheduled_date: date


class UpcomingReader:
    def __init__(self, uow: RecurrencesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def list_upcoming(self, from_date: date, to_date: date) -> list[UpcomingItem]:
        async with self._uow as uow:
            recurrences_with_names = await uow.recurrences.get_active_due_in_range(
                from_date, to_date
            )

        results: list[UpcomingItem] = []
        year, month = from_date.year, from_date.month
        months: list[tuple[int, int]] = []
        while (year, month) <= (to_date.year, to_date.month):
            months.append((year, month))
            month += 1
            if month > 12:
                month = 1
                year += 1

        for rec, client_name in recurrences_with_names:
            for y, m in months:
                emission_date = resolve_emission_date(y, m, rec.day_of_month)
                if from_date <= emission_date <= to_date:
                    results.append(
                        UpcomingItem(
                            recurrence_id=rec.id,
                            client_id=rec.client_id,
                            client_name=client_name,
                            amount=rec.amount,
                            description=rec.description,
                            scheduled_date=emission_date,
                        )
                    )

        results.sort(key=lambda x: (x.scheduled_date, x.client_name))
        return results

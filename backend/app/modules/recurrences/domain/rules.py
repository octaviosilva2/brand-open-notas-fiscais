# app/modules/recurrences/domain/rules.py
from calendar import monthrange
from datetime import date

from app.modules.recurrences.domain.entities import Recurrence


def resolve_emission_date(year: int, month: int, day_of_month: int) -> date:
    """Resolve a data de emissão respeitando os limites do mês."""
    last_day = monthrange(year, month)[1]
    return date(year, month, min(day_of_month, last_day))


def is_due_on(recurrence: Recurrence, target_date: date) -> bool:
    """Retorna True se a recorrência deve ser emitida na data alvo."""
    if not recurrence.is_active:
        return False
    if target_date < recurrence.start_date:
        return False
    if recurrence.end_date and target_date > recurrence.end_date:
        return False
    emission_date = resolve_emission_date(
        target_date.year, target_date.month, recurrence.day_of_month
    )
    return emission_date == target_date

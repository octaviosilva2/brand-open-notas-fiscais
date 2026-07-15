# tests/unit/modules/recurrences/test_rules.py
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from app.modules.recurrences.domain.entities import Recurrence
from app.modules.recurrences.domain.rules import is_due_on, resolve_emission_date


def _make_recurrence(
    day_of_month: int = 15,
    start_date: date = date(2026, 1, 1),
    end_date: date | None = None,
    is_active: bool = True,
) -> Recurrence:
    return Recurrence(
        id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        description="Serviço",
        amount=Decimal("100.00"),
        day_of_month=day_of_month,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
        inf_dps={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_resolve_emission_date_normal():
    assert resolve_emission_date(2026, 3, 15) == date(2026, 3, 15)


def test_resolve_emission_date_day_31_in_february_non_leap():
    assert resolve_emission_date(2026, 2, 31) == date(2026, 2, 28)


def test_resolve_emission_date_day_31_in_february_leap():
    assert resolve_emission_date(2028, 2, 31) == date(2028, 2, 29)


def test_resolve_emission_date_day_31_in_march():
    assert resolve_emission_date(2026, 3, 31) == date(2026, 3, 31)


def test_resolve_emission_date_day_31_in_april():
    assert resolve_emission_date(2026, 4, 31) == date(2026, 4, 30)


def test_resolve_emission_date_day_28_in_february():
    assert resolve_emission_date(2026, 2, 28) == date(2026, 2, 28)


def test_is_due_on_inactive():
    rec = _make_recurrence(day_of_month=15, is_active=False)
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_before_start_date():
    rec = _make_recurrence(day_of_month=15, start_date=date(2026, 7, 1))
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_after_end_date():
    rec = _make_recurrence(day_of_month=15, end_date=date(2026, 5, 31))
    assert is_due_on(rec, date(2026, 6, 15)) is False


def test_is_due_on_correct_day():
    rec = _make_recurrence(day_of_month=15)
    assert is_due_on(rec, date(2026, 6, 15)) is True


def test_is_due_on_wrong_day():
    rec = _make_recurrence(day_of_month=15)
    assert is_due_on(rec, date(2026, 6, 16)) is False


def test_is_due_on_day_31_february():
    rec = _make_recurrence(day_of_month=31)
    assert is_due_on(rec, date(2026, 2, 28)) is True
    assert is_due_on(rec, date(2026, 2, 27)) is False


def test_is_due_on_no_end_date():
    rec = _make_recurrence(day_of_month=1, end_date=None)
    assert is_due_on(rec, date(2030, 12, 1)) is True

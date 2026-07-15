# app/modules/recurrences/adapters/db/factories.py
from app.core.db.session import db
from app.modules.recurrences.adapters.db.unit_of_work import RecurrencesUnitOfWork


def make_unit_of_work() -> RecurrencesUnitOfWork:
    return RecurrencesUnitOfWork(session_factory=db.create_session)

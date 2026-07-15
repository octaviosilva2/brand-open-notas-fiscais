# app/modules/invoices/adapters/db/factories.py
from app.core.db.session import db
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork


def make_unit_of_work() -> InvoicesUnitOfWork:
    return InvoicesUnitOfWork(session_factory=db.create_session)

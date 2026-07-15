from app.core.db.session import db
from app.core.db.unit_of_work import BaseUnitOfWork


def get_unit_of_work():
    """Dependência para obter uma instância de UnitOfWork."""

    session = db.create_session()
    return BaseUnitOfWork(session)

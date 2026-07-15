# app/modules/invoices/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.modules.invoices.adapters.db.factories import make_unit_of_work
from app.modules.invoices.adapters.db.unit_of_work import InvoicesUnitOfWork
from app.modules.invoices.adapters.http.schemas import InvoicesPaginationFilters
from app.modules.invoices.application.dtos.filters import InvoiceFilters

# Dependência tipada para o UoW de invoices
InvoicesUnitOfWorkDep = Annotated[InvoicesUnitOfWork, Depends(make_unit_of_work)]


def get_invoice_filters(
    query_params: Annotated[InvoicesPaginationFilters, Depends()],
) -> InvoiceFilters:
    """Converte os query params de paginação no DTO interno de filtros."""
    return InvoiceFilters(
        status=query_params.status,
        client_id=query_params.client_id,
        from_date=query_params.from_date,
        to_date=query_params.to_date,
    )


# Dependência tipada para os filtros de invoices
InvoiceFiltersDep = Annotated[InvoiceFilters, Depends(get_invoice_filters)]

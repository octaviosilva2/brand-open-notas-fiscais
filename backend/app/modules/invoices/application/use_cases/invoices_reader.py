# app/modules/invoices/application/use_cases/invoices_reader.py
import uuid
from datetime import date, timedelta

from app.modules.invoices.application.dtos.filters import InvoiceFilters
from app.modules.invoices.application.ports.unit_of_work import (
    InvoicesUnitOfWorkProtocol,
)
from app.modules.invoices.domain.entities import Invoice


class InvoicesReader:
    def __init__(self, uow: InvoicesUnitOfWorkProtocol) -> None:
        self._uow = uow

    async def get_by_id(self, id_: uuid.UUID) -> tuple[Invoice, str]:
        """Busca uma invoice por ID retornando a entidade e o nome do cliente."""
        async with self._uow as uow:
            return await uow.invoices.get_with_client_name(id_)

    async def list_paginated(
        self,
        filters: InvoiceFilters,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Invoice, str]], int]:
        """
        Lista invoices paginadas com filtros opcionais.
        Se from_date/to_date não forem fornecidos, usa intervalo padrão de 30 dias.
        """
        today = date.today()
        effective_from = filters.from_date or (today - timedelta(days=30))
        effective_to = filters.to_date or today

        # Aplica datas efetivas preservando outros filtros
        effective_filters = InvoiceFilters(
            status=filters.status,
            client_id=filters.client_id,
            from_date=effective_from,
            to_date=effective_to,
        )

        async with self._uow as uow:
            return await uow.invoices.paginate_with_client_name(
                effective_filters, page, page_size
            )

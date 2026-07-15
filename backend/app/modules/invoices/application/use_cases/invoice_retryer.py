# app/modules/invoices/application/use_cases/invoice_retryer.py
import uuid
from datetime import UTC, datetime, timedelta

from app.core.exceptions import ConflictError
from app.core.settings import settings
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.poller import DpsPoller
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.invoices.application.dtos.commands import UpdateInvoiceCommand
from app.modules.invoices.application.ports.unit_of_work import (
    InvoicesUnitOfWorkProtocol,
)
from app.modules.invoices.domain.entities import Invoice
from app.modules.recurrences.adapters.db.factories import (
    make_unit_of_work as make_recurrences_uow,
)


class InvoiceRetryer:
    def __init__(
        self,
        uow: InvoicesUnitOfWorkProtocol,
        poller: DpsPoller | None = None,
        clients_uow_factory=None,
        recurrences_uow_factory=None,
    ) -> None:
        self._uow = uow
        self._poller = poller or DpsPoller()
        self._clients_uow_factory = clients_uow_factory or make_clients_uow
        self._recurrences_uow_factory = recurrences_uow_factory or make_recurrences_uow

    async def retry(self, invoice_id: uuid.UUID) -> tuple[Invoice, str]:
        """
        Retenta a emissão de uma NFS-e para invoices com status 'error'
        ou 'processing' travado (> 10 minutos sem atualização).
        """
        # Valida e reseta o status para 'pending'
        async with self._uow as uow:
            invoice, client_name = await uow.invoices.get_with_client_name(invoice_id)
            self._validate_retryable(invoice)

            await uow.invoices.update(
                invoice_id,
                UpdateInvoiceCommand(
                    status="pending",
                    protocol=None,
                    nf_number=None,
                    pdf_url=None,
                    xml_sent=None,
                    xml_response=None,
                    error_message=None,
                    emission_date=None,
                ),
            )

            # Obtém próximo número DPS dentro da mesma transação
            n_dps = await next_n_dps(uow.session, settings.BETHA_SERIE)  # type: ignore[attr-defined]

        # Carrega dados do cliente
        clients_uow = self._clients_uow_factory()
        async with clients_uow as cuow:
            client = await cuow.clients.get_by_id(invoice.client_id)

        # Carrega dados da recorrência
        recurrences_uow = self._recurrences_uow_factory()
        async with recurrences_uow as ruow:
            recurrence = await ruow.recurrences.get_by_id(invoice.recurrence_id)

        # Monta payload e emite via integração Betha
        payload = DpsPayload(
            recurrence_id=invoice.recurrence_id,
            client=client,
            recurrence=recurrence,
            emission_date=invoice.scheduled_date,
            n_dps=n_dps,
        )

        result: EmissionResult = await self._poller.emit_and_poll(payload)

        # Persiste resultado da emissão
        now = datetime.now(UTC)
        async with self._uow as uow:
            updated = await uow.invoices.update(
                invoice_id,
                UpdateInvoiceCommand(
                    status="success" if result.ok else "error",
                    n_dps=n_dps,
                    protocol=result.protocol,
                    nf_number=result.nf_number,
                    pdf_url=result.pdf_url,
                    xml_sent=result.xml_sent or None,
                    xml_response=result.xml_response or None,
                    error_message=result.error_message,
                    emission_date=now if result.ok else None,
                ),
            )
            _, client_name = await uow.invoices.get_with_client_name(invoice_id)

        return updated, client_name

    def _validate_retryable(self, invoice: Invoice) -> None:
        """
        Valida se a invoice pode ser reprocessada. Permite retry apenas para status
        'error' ou 'processing' travado há mais de 10 min.
        """
        if invoice.status == "error":
            return

        if invoice.status == "processing":
            staleness_threshold = datetime.now(UTC) - timedelta(minutes=10)
            if invoice.updated_at < staleness_threshold:
                return

        raise ConflictError("Esta nota não está disponível para reprocessamento.")

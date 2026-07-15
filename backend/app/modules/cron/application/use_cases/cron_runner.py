# app/modules/cron/application/use_cases/cron_runner.py
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.core.db.session import db
from app.core.settings import settings
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.poller import DpsPoller
from app.modules.clients.adapters.db.factories import (
    make_unit_of_work as make_clients_uow,
)
from app.modules.cron.application.notification_service import (
    NotificationItem,
    NotificationService,
)
from app.modules.invoices.adapters.db.factories import (
    make_unit_of_work as make_invoices_uow,
)
from app.modules.invoices.domain.entities import NewInvoice, UpdateInvoice
from app.modules.recurrences.adapters.db.factories import (
    make_unit_of_work as make_recurrences_uow,
)
from app.modules.recurrences.domain.entities import Recurrence
from app.modules.recurrences.domain.rules import is_due_on

logger = logging.getLogger(__name__)


@dataclass
class CronItemResult:
    recurrence_id: str
    client_name: str
    invoice_id: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


@dataclass
class CronResult:
    date: date
    total: int
    success: int
    error: int
    results: list[CronItemResult] = field(default_factory=list)


class CronRunner:
    def __init__(
        self,
        poller: DpsPoller | None = None,
        notification_service: NotificationService | None = None,
        recurrences_uow_factory=None,
        invoices_uow_factory=None,
        clients_uow_factory=None,
    ) -> None:
        self._poller = poller or DpsPoller()
        self._notification = notification_service or NotificationService()
        self._recurrences_uow_factory = recurrences_uow_factory or make_recurrences_uow
        self._invoices_uow_factory = invoices_uow_factory or make_invoices_uow
        self._clients_uow_factory = clients_uow_factory or make_clients_uow

    async def run(self, target_date: date) -> CronResult:
        # Busca recorrências ativas no range da data alvo
        recurrences_uow = self._recurrences_uow_factory()
        async with recurrences_uow as ruow:
            all_recurrences = await ruow.recurrences.get_active_due_in_range(
                target_date, target_date
            )

        # Filtra apenas as que vencem exatamente na data alvo
        due = [rec for rec in all_recurrences if is_due_on(rec[0], target_date)]

        results: list[CronItemResult] = []
        notification_items: list[NotificationItem] = []

        for recurrence in due:
            item = await self._process_one(recurrence[0], target_date)
            results.append(item)
            notification_items.append(
                NotificationItem(
                    client_name=item.client_name,
                    ok=item.ok,
                    nf_number=item.nf_number,
                    pdf_url=item.pdf_url,
                    error_message=item.error_message,
                )
            )

        await self._notification.send_summary(target_date, notification_items)

        successes = sum(1 for r in results if r.ok)
        return CronResult(
            date=target_date,
            total=len(results),
            success=successes,
            error=len(results) - successes,
            results=results,
        )

    async def _process_one(
        self,
        recurrence: Recurrence,
        target_date: date,
    ) -> CronItemResult:
        invoices_uow = self._invoices_uow_factory()

        # Busca o cliente para obter o nome
        clients_uow = self._clients_uow_factory()
        async with clients_uow as cuow:
            client = await cuow.clients.get_by_id(recurrence.client_id)
        client_name = client.name

        try:
            async with invoices_uow as iuow:
                existing = await iuow.invoices.get_by_recurrence_and_date(
                    recurrence.id, target_date
                )

            # Idempotência: pula emissões já bem-sucedidas
            if existing and existing.status == "success":
                logger.info(f"Invoice {existing.id} já emitido com sucesso. Pulando.")
                return CronItemResult(
                    recurrence_id=str(recurrence.id),
                    client_name=client_name,
                    invoice_id=str(existing.id),
                    ok=True,
                    nf_number=existing.nf_number,
                    pdf_url=existing.pdf_url,
                )

            # Cria ou reinicia a invoice
            async with invoices_uow as iuow:
                if existing:
                    # Reinicia invoice com erro anterior para nova tentativa
                    await iuow.invoices.update(
                        existing.id,
                        UpdateInvoice(
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
                    invoice_id = existing.id
                else:
                    # Cria nova invoice no estado pending
                    inv = await iuow.invoices.create(
                        NewInvoice(
                            recurrence_id=recurrence.id,
                            client_id=recurrence.client_id,
                            scheduled_date=target_date,
                            amount=recurrence.amount,
                            description=recurrence.description,
                        )
                    )
                    invoice_id = inv.id

            # Marca como processing antes de emitir
            async with invoices_uow as iuow:
                await iuow.invoices.update(
                    invoice_id, UpdateInvoice(status="processing")
                )

            # Obtém o próximo número de DPS atomicamente
            session = db.create_session()
            async with session as sess:
                n_dps = await next_n_dps(sess, settings.BETHA_SERIE)
                await sess.commit()

            # Monta o payload e emite a NFS-e
            payload = DpsPayload(
                recurrence_id=recurrence.id,
                client=client,
                recurrence=recurrence,
                emission_date=target_date,
                n_dps=n_dps,
            )
            result: EmissionResult = await self._poller.emit_and_poll(payload)

            # Atualiza a invoice com o resultado da emissão
            now = datetime.now(UTC)
            async with invoices_uow as iuow:
                await iuow.invoices.update(
                    invoice_id,
                    UpdateInvoice(
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

            return CronItemResult(
                recurrence_id=str(recurrence.id),
                client_name=client_name,
                invoice_id=str(invoice_id),
                ok=result.ok,
                nf_number=result.nf_number,
                pdf_url=result.pdf_url,
                error_message=result.error_message,
            )

        except Exception as exc:
            logger.exception(f"Erro ao processar recorrência {recurrence.id}: {exc}")
            return CronItemResult(
                recurrence_id=str(recurrence.id),
                client_name=client_name,
                invoice_id="",
                ok=False,
                error_message=str(exc),
            )

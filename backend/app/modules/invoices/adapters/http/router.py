# app/modules/invoices/adapters/http/router.py
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, Response

from app.core.exceptions import NotFoundError
from app.core.pagination.schemas import PaginatedResponse, build_paginated_response
from app.modules.invoices.adapters.http.dependencies import (
    InvoiceFiltersDep,
    InvoicesUnitOfWorkDep,
)
from app.modules.invoices.adapters.http.schemas import (
    InvoiceDetailRead,
    InvoiceRead,
)
from app.modules.invoices.application.use_cases.invoice_retryer import InvoiceRetryer
from app.modules.invoices.application.use_cases.invoices_reader import InvoicesReader
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("", response_model=PaginatedResponse[InvoiceRead])
async def list_invoices(
    filters: InvoiceFiltersDep,
    uow: InvoicesUnitOfWorkDep,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[InvoiceRead]:
    """Lista invoices com filtros opcionais e paginação."""
    reader = InvoicesReader(uow=uow)
    items, total = await reader.list_paginated(filters, page, page_size)
    return build_paginated_response(
        items=[InvoiceRead.model_validate(inv.to_dict(cn)) for inv, cn in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{invoice_id}", response_model=InvoiceDetailRead)
async def get_invoice(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> InvoiceDetailRead:
    """Retorna os detalhes de uma invoice, incluindo XML enviado e recebido."""
    reader = InvoicesReader(uow=uow)
    invoice, client_name = await reader.get_by_id(invoice_id)
    return InvoiceDetailRead.model_validate(invoice.to_dict(client_name))


@router.get("/{invoice_id}/xml")
async def get_invoice_xml(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> Response:
    """Faz download do XML enviado para emissão da NFS-e."""
    reader = InvoicesReader(uow=uow)
    invoice, _ = await reader.get_by_id(invoice_id)
    if not invoice.xml_sent:
        raise NotFoundError("XML não disponível para esta nota.")
    filename = f"dps_{invoice.n_dps or invoice_id}.xml"
    return Response(
        content=invoice.xml_sent,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> RedirectResponse:
    """Redireciona para a URL do PDF da NFS-e."""
    reader = InvoicesReader(uow=uow)
    invoice, _ = await reader.get_by_id(invoice_id)
    if not invoice.pdf_url:
        raise NotFoundError("PDF não disponível para esta nota.")
    return RedirectResponse(url=invoice.pdf_url, status_code=302)


@router.post("/{invoice_id}/retry", response_model=InvoiceRead)
async def retry_invoice(
    invoice_id: uuid.UUID,
    uow: InvoicesUnitOfWorkDep,
) -> InvoiceRead:
    """Retenta a emissão de uma NFS-e com status 'error' ou 'processing' travado."""
    retryer = InvoiceRetryer(uow=uow)
    invoice, client_name = await retryer.retry(invoice_id)
    return InvoiceRead.model_validate(invoice.to_dict(client_name))

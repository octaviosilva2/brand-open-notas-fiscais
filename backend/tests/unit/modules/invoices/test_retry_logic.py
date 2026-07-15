# tests/unit/modules/invoices/test_retry_logic.py
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.exceptions import ConflictError
from app.modules.invoices.application.use_cases.invoice_retryer import InvoiceRetryer
from app.modules.invoices.domain.entities import Invoice


def _make_invoice(
    status: str,
    updated_at: datetime | None = None,
) -> Invoice:
    """Cria uma invoice de teste com o status e updated_at informados."""
    now = updated_at or datetime.now(UTC)
    return Invoice(
        id=uuid.uuid4(),
        recurrence_id=uuid.uuid4(),
        client_id=uuid.uuid4(),
        scheduled_date=date(2026, 6, 15),
        amount=Decimal("1500.00"),
        description="Serviço",
        status=status,
        n_dps=None,
        protocol=None,
        nf_number=None,
        pdf_url=None,
        xml_sent=None,
        xml_response=None,
        error_message=None,
        emission_date=None,
        created_at=now,
        updated_at=now,
    )


def _get_retryer() -> InvoiceRetryer:
    """Instancia o retryer sem UoW real (apenas para testar _validate_retryable)."""
    return InvoiceRetryer(uow=None)  # type: ignore[arg-type]


def test_validate_error_status_is_retryable():
    """Invoice com status 'error' deve ser aceita para retry."""
    invoice = _make_invoice("error")
    retryer = _get_retryer()
    retryer._validate_retryable(invoice)  # não deve lançar


def test_validate_success_status_raises_conflict():
    """Invoice com status 'success' não pode ser reprocessada."""
    invoice = _make_invoice("success")
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_pending_status_raises_conflict():
    """Invoice com status 'pending' não pode ser reprocessada."""
    invoice = _make_invoice("pending")
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_processing_recent_raises_conflict():
    """Invoice 'processing' atualizada há menos de 10 min não pode ser reprocessada."""
    recent = datetime.now(UTC) - timedelta(minutes=5)
    invoice = _make_invoice("processing", updated_at=recent)
    retryer = _get_retryer()
    with pytest.raises(ConflictError):
        retryer._validate_retryable(invoice)


def test_validate_processing_stale_is_retryable():
    """Invoice 'processing' travada há mais de 10 min pode ser reprocessada."""
    stale = datetime.now(UTC) - timedelta(minutes=15)
    invoice = _make_invoice("processing", updated_at=stale)
    retryer = _get_retryer()
    retryer._validate_retryable(invoice)  # não deve lançar

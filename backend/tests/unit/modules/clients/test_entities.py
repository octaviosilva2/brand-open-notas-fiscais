# tests/unit/modules/clients/test_entities.py
import re
import uuid
from datetime import UTC, datetime

import pytest

from app.modules.clients.domain.entities import Client


def _make_client(document: str) -> Client:
    return Client(
        id=uuid.uuid4(),
        document=document,
        name="Empresa Teste",
        municipal_registration=None,
        phone=None,
        email=None,
        zip_code=None,
        street=None,
        number=None,
        complement=None,
        neighborhood=None,
        ibge_city_code=None,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_document_type_cpf():
    client = _make_client("12345678901")
    assert client.document_type == "CPF"


def test_document_type_cnpj():
    client = _make_client("12345678000195")
    assert client.document_type == "CNPJ"


def _validate_document(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) not in (11, 14):
        raise ValueError("CPF deve ter 11 dígitos e CNPJ 14 dígitos.")
    return digits


def test_validate_document_strips_mask():
    assert _validate_document("123.456.789-01") == "12345678901"


def test_validate_document_cnpj_strips_mask():
    assert _validate_document("12.345.678/0001-95") == "12345678000195"


def test_validate_document_invalid_length():
    with pytest.raises(ValueError, match="CPF deve ter 11"):
        _validate_document("1234567890")


def test_validate_document_13_digits_invalid():
    with pytest.raises(ValueError, match="CPF deve ter 11"):
        _validate_document("1234567890123")

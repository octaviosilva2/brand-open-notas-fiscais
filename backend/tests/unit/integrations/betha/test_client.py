# tests/unit/integrations/betha/test_client.py
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.betha.client import BethaClient
from app.integrations.betha.exceptions import BethaError

_NS = "http://www.betha.com.br/e-nota-dps"


def _make_client(response_xml: str) -> BethaClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=response_xml)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return BethaClient(http)


_RECEPCAO_OK = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soapenv:Body>"
    f'<dps:RecepcionarDpsResposta xmlns:dps="{_NS}">'
    "<dps:protocolo>1abc123</dps:protocolo>"
    "<dps:dhRecebimento>2026-01-15T10:00:01</dps:dhRecebimento>"
    "<dps:status>Aguardando validação do ambiente nacional</dps:status>"
    "</dps:RecepcionarDpsResposta>"
    "</soapenv:Body>"
    "</soapenv:Envelope>"
)

_RECEPCAO_REJEITADA = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soapenv:Body>"
    f'<dps:RecepcionarDpsResposta xmlns:dps="{_NS}">'
    "<dps:protocolo></dps:protocolo>"
    "<dps:dhRecebimento>2026-01-15T10:00:01</dps:dhRecebimento>"
    "<dps:status>Rejeitado</dps:status>"
    "<dps:listaMensagens>"
    "<dps:mensagem>"
    "<dps:codigo>E022</dps:codigo>"
    "<dps:mensagem>CNPJ do prestador inválido</dps:mensagem>"
    "<dps:correcao>Verifique o CNPJ informado</dps:correcao>"
    "</dps:mensagem>"
    "</dps:listaMensagens>"
    "</dps:RecepcionarDpsResposta>"
    "</soapenv:Body>"
    "</soapenv:Envelope>"
)


def _status_response(status: str, extra: str = "") -> str:
    return (
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">'
        "<SOAP-ENV:Body>"
        f'<ns2:ConsultarStatusDpsEmissaoResposta xmlns:ns2="{_NS}">'
        f"<ns2:statusProcessamento>{status}</ns2:statusProcessamento>"
        "<ns2:dataHoraRecebimento>2026-01-15T10:51:14-03:00</ns2:dataHoraRecebimento>"
        "<ns2:protocolo>PROTO123</ns2:protocolo>"
        f"{extra}"
        "</ns2:ConsultarStatusDpsEmissaoResposta>"
        "</SOAP-ENV:Body>"
        "</SOAP-ENV:Envelope>"
    )


@pytest.fixture(autouse=True)
def _no_disk_logs():
    with patch("app.integrations.betha.client.log_betha_exchange", new=AsyncMock()):
        yield


async def test_submit_dps_retorna_protocolo():
    client = _make_client(_RECEPCAO_OK)
    protocol = await client.submit_dps("<xml/>")
    assert protocol == "1abc123"


async def test_submit_dps_rejeitado_levanta_erro_com_mensagens():
    client = _make_client(_RECEPCAO_REJEITADA)
    with pytest.raises(BethaError) as exc:
        await client.submit_dps("<xml/>")
    assert "E022" in str(exc.value)
    assert "CNPJ do prestador inválido" in str(exc.value)


async def test_check_status_processado_com_sucesso():
    extra = (
        "<ns2:idDps>DPS001</ns2:idDps>"
        "<ns2:numeroNotaFiscal>198954</ns2:numeroNotaFiscal>"
        "<ns2:linkPdf>https://notas.prefeitura.gov.br/pdf/NF-12345.pdf</ns2:linkPdf>"
    )
    client = _make_client(_status_response("Processado com sucesso", extra))
    result = await client.check_status("PROTO123")
    assert result.status == "PROCESSADO"
    assert result.nf_number == "198954"
    assert result.pdf_url == "https://notas.prefeitura.gov.br/pdf/NF-12345.pdf"


async def test_check_status_processado_com_erro():
    extra = "<ns2:mensagemErro>Mensagem de erro</ns2:mensagemErro>"
    client = _make_client(_status_response("Processado com erro", extra))
    result = await client.check_status("PROTO123")
    assert result.status == "ERRO"
    assert result.error_message == "Mensagem de erro"


async def test_check_status_aguardando_validacao():
    client = _make_client(_status_response("Aguardando validação do ambiente nacional"))
    result = await client.check_status("PROTO123")
    assert result.status == "AGUARDANDO"

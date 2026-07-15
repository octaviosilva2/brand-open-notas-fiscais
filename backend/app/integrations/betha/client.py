# app/integrations/betha/client.py
import xml.etree.ElementTree as ET

import httpx

from app.core.settings import settings
from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import PollResult
from app.integrations.betha.payload_logger import log_betha_exchange

_NS = "http://www.betha.com.br/e-nota-dps"

# Textos de statusProcessamento retornados pela Betha na consulta de status
# (documentação "DPS por Web Service - Nota Nacional").
_STATUS_SUCESSO = "processado com sucesso"
_STATUS_ERRO = "processado com erro"


def _build_status_envelope(protocol: str) -> str:
    return (
        f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:e="{_NS}">'
        f"<soapenv:Body>"
        f"<e:ConsultarStatusDpsEnvio>"
        f"<e:tpAmb>{settings.BETHA_ENV}</e:tpAmb>"
        f"<e:codigoIbge>{settings.CITY_CODE}</e:codigoIbge>"
        f"<e:cpfCnpjPrestador>{settings.EMITTER_CNPJ}</e:cpfCnpjPrestador>"
        f"<e:protocolo>{protocol}</e:protocolo>"
        f"<e:tipoIntegracao>EMISSAO</e:tipoIntegracao>"
        f"</e:ConsultarStatusDpsEnvio>"
        f"</soapenv:Body>"
        f"</soapenv:Envelope>"
    )


def _collect_error_messages(root: ET.Element) -> str | None:
    """Extrai mensagens de `listaMensagens` (codigo/mensagem/correcao)."""
    parts: list[str] = []
    for msg_el in root.findall(f".//{{{_NS}}}listaMensagens/{{{_NS}}}mensagem"):
        codigo = msg_el.findtext(f"{{{_NS}}}codigo") or ""
        texto = msg_el.findtext(f"{{{_NS}}}mensagem") or ""
        correcao = msg_el.findtext(f"{{{_NS}}}correcao") or ""
        item = f"{codigo}: {texto}".strip(": ")
        if correcao:
            item = f"{item} ({correcao})"
        if item:
            parts.append(item)
    return "; ".join(parts) or None


class BethaClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def submit_dps(self, xml_envelope: str) -> str:
        """Envia DPS e retorna o protocolo."""
        resp = await self._http.post(
            settings.BETHA_WSDL_URL,
            content=xml_envelope.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '""',
            },
        )
        await log_betha_exchange("submit_dps", xml_envelope, resp.text)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)

        protocol_el = root.find(".//{*}protocolo")
        if protocol_el is None or not protocol_el.text:
            msg = _collect_error_messages(root) or resp.text
            raise BethaError(f"Betha não retornou protocolo: {msg}")
        return protocol_el.text

    async def check_status(self, protocol: str) -> PollResult:
        """Consulta status de processamento pelo protocolo.

        A resposta (`ConsultarStatusDpsEmissaoResposta`) traz
        `statusProcessamento` com um dos textos: "Processado com sucesso",
        "Processado com erro" ou "Aguardando validação do ambiente nacional".
        """
        envelope = _build_status_envelope(protocol)
        resp = await self._http.post(
            settings.BETHA_WSDL_URL,
            content=envelope.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": '""',
            },
        )
        raw = resp.text
        await log_betha_exchange("check_status", envelope, raw)
        resp.raise_for_status()
        root = ET.fromstring(raw)

        status_el = root.find(".//{*}statusProcessamento")
        status_text = (
            (status_el.text or "").strip().lower() if status_el is not None else ""
        )

        if status_text == _STATUS_SUCESSO:
            nf_el = root.find(".//{*}numeroNotaFiscal")
            pdf_el = root.find(".//{*}linkPdf")
            return PollResult(
                status="PROCESSADO",
                nf_number=nf_el.text if nf_el is not None else None,
                pdf_url=pdf_el.text if pdf_el is not None else None,
                raw_response=raw,
            )

        if status_text == _STATUS_ERRO:
            err_el = root.find(".//{*}mensagemErro")
            error_message = (
                err_el.text
                if err_el is not None and err_el.text
                else _collect_error_messages(root)
            )
            return PollResult(
                status="ERRO",
                error_message=error_message,
                raw_response=raw,
            )

        return PollResult(status="AGUARDANDO", raw_response=raw)

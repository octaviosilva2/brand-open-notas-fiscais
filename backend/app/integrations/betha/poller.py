# app/integrations/betha/poller.py
import asyncio
import ssl
import tempfile

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.integrations.betha.client import BethaClient
from app.integrations.betha.counter import next_n_dps
from app.integrations.betha.exceptions import BethaError
from app.integrations.betha.models import DpsPayload, EmissionResult
from app.integrations.betha.xml_builder import DpsXmlBuilder
from app.integrations.betha.xml_signer import DpsXmlSigner


def _make_http_client() -> httpx.AsyncClient:
    """Cria AsyncClient com mTLS quando BETHA_CERT_PATH está configurado."""
    if not settings.BETHA_CERT_PATH:
        return httpx.AsyncClient(timeout=30.0)

    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        pkcs12,
    )

    password = (settings.BETHA_CERT_PASSWORD or "").encode()
    with open(settings.BETHA_CERT_PATH, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_data, password)
    if private_key is None or certificate is None:
        raise RuntimeError("Certificado PFX inválido: chave ou certificado ausente.")

    key_pem = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
    )
    cert_pem = certificate.public_bytes(Encoding.PEM)

    ctx = ssl.create_default_context()
    with (
        tempfile.NamedTemporaryFile(suffix=".pem") as cert_f,
        tempfile.NamedTemporaryFile(suffix=".pem") as key_f,
    ):
        cert_f.write(cert_pem)
        cert_f.flush()
        key_f.write(key_pem)
        key_f.flush()
        ctx.load_cert_chain(certfile=cert_f.name, keyfile=key_f.name)

    return httpx.AsyncClient(timeout=30.0, verify=ctx)


class DpsPoller:
    def __init__(
        self,
        builder: DpsXmlBuilder | None = None,
        signer: DpsXmlSigner | None = None,
        client: BethaClient | None = None,
    ) -> None:
        self._builder = builder or DpsXmlBuilder()
        self._signer = signer or DpsXmlSigner()
        self._client = client

    async def emit_and_poll(
        self,
        payload: DpsPayload,
    ) -> EmissionResult:
        xml = self._builder.build(payload)
        xml = self._signer.sign(xml)

        async with _make_http_client() as http:
            betha = self._client or BethaClient(http)

            try:
                protocol = await betha.submit_dps(xml)
            except BethaError as e:
                return EmissionResult(ok=False, xml_sent=xml, error_message=str(e))
            except Exception as e:
                return EmissionResult(
                    ok=False, xml_sent=xml, error_message=f"Erro inesperado: {e}"
                )

            for _ in range(settings.BETHA_POLL_MAX_ATTEMPTS):
                await asyncio.sleep(settings.BETHA_POLL_INTERVAL_S)
                try:
                    result = await betha.check_status(protocol)
                except Exception as e:
                    return EmissionResult(
                        ok=False,
                        protocol=protocol,
                        xml_sent=xml,
                        error_message=f"Erro no polling: {e}",
                    )

                if result.status == "PROCESSADO":
                    return EmissionResult(
                        ok=True,
                        protocol=protocol,
                        nf_number=result.nf_number,
                        pdf_url=result.pdf_url,
                        xml_sent=xml,
                        xml_response=result.raw_response,
                    )

                if result.status == "ERRO":
                    return EmissionResult(
                        ok=False,
                        protocol=protocol,
                        xml_sent=xml,
                        xml_response=result.raw_response,
                        error_message=result.error_message,
                    )

        return EmissionResult(
            ok=False,
            protocol=protocol,
            xml_sent=xml,
            error_message="Timeout ao aguardar processamento da Betha.",
        )


async def get_next_n_dps(session: AsyncSession, serie: str) -> int:
    """Conveniência para obter próximo nDPS a partir de uma sessão."""
    return await next_n_dps(session, serie)

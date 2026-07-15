# app/integrations/betha/xml_signer.py
import base64

from cryptography.x509 import Certificate
from lxml.etree import _Element

from app.core.settings import settings

_NS = "http://www.betha.com.br/e-nota-dps"
_DSIG = "http://www.w3.org/2000/09/xmldsig#"


def _build_key_info(certificate: Certificate) -> _Element:
    """Constrói KeyInfo contendo apenas X509Certificate (sem SubjectName/KeyValue)."""
    from cryptography.hazmat.primitives.serialization import Encoding
    from lxml import etree

    ki: _Element = etree.Element(f"{{{_DSIG}}}KeyInfo")
    x509_data = etree.SubElement(ki, f"{{{_DSIG}}}X509Data")
    x509_cert_el = etree.SubElement(x509_data, f"{{{_DSIG}}}X509Certificate")
    der = certificate.public_bytes(Encoding.DER)
    x509_cert_el.text = base64.b64encode(der).decode()
    return ki


class DpsXmlSigner:
    def sign(self, xml: str) -> str:
        """Retorna o XML assinado com XMLDSig enveloped (RSA-SHA256).

        Em homologação sem certificado configurado, retorna inalterado.
        """
        if not settings.BETHA_CERT_PATH:
            return xml

        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            pkcs12,
        )
        from lxml import etree
        from signxml import XMLSigner, methods  # type: ignore[attr-defined]

        password = (settings.BETHA_CERT_PASSWORD or "").encode()
        with open(settings.BETHA_CERT_PATH, "rb") as f:
            pfx_data = f.read()

        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data, password
        )
        if private_key is None or certificate is None:
            raise RuntimeError(
                "Certificado PFX inválido: chave ou certificado ausente."
            )

        key_pem = private_key.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        )

        root: _Element = etree.fromstring(xml.encode())

        dps = root.find(f".//{{{_NS}}}DPS")
        if dps is None:
            return xml

        inf_dps = dps.find(f"{{{_NS}}}infDPS")
        if inf_dps is None:
            return xml

        inf_dps_id = inf_dps.get("id", "")
        key_info = _build_key_info(certificate)

        signer: XMLSigner = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
        )

        dps_parent = dps.getparent()
        dps_idx = list(dps_parent).index(dps) if dps_parent is not None else -1

        signed_dps: _Element = signer.sign(
            dps,
            key=key_pem,
            key_info=key_info,
            reference_uri=f"#{inf_dps_id}",
            id_attribute="id",
        )

        if dps_parent is not None and signed_dps is not dps:
            dps_parent.remove(dps)
            dps_parent.insert(dps_idx, signed_dps)

        return etree.tostring(root, encoding="unicode")

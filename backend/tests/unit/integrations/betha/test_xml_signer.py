# tests/unit/integrations/betha/test_xml_signer.py
from unittest.mock import patch

from cryptography.hazmat.primitives.serialization import Encoding
from lxml import etree

_NS = "http://www.betha.com.br/e-nota-dps"
_DSIG = "http://www.w3.org/2000/09/xmldsig#"

_INF_DPS_ID = "DPS4204608112223330001810090000000000000001"

_SAMPLE_XML = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
    f' xmlns="{_NS}">'
    "<soapenv:Header/>"
    "<soapenv:Body>"
    "<RecepcionarDpsEnvio>"
    '<DPS versao="1.01">'
    f'<infDPS id="{_INF_DPS_ID}">'
    "<tpAmb>2</tpAmb>"
    "</infDPS>"
    "</DPS>"
    "</RecepcionarDpsEnvio>"
    "</soapenv:Body>"
    "</soapenv:Envelope>"
)


def test_sign_sem_cert_retorna_xml_original():
    from app.integrations.betha.xml_signer import DpsXmlSigner

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    assert result == _SAMPLE_XML


def test_sign_com_cert_adiciona_signature(test_cert):
    pfx_path, _ = test_cert
    from app.integrations.betha.xml_signer import DpsXmlSigner

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    root = etree.fromstring(result.encode())
    assert root.find(f".//{{{_DSIG}}}Signature") is not None


def test_sign_signature_e_filho_direto_de_dps(test_cert):
    pfx_path, _ = test_cert
    from app.integrations.betha.xml_signer import DpsXmlSigner

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    root = etree.fromstring(result.encode())
    dps = root.find(f".//{{{_NS}}}DPS")
    assert dps is not None
    child_tags = [c.tag for c in dps]
    assert f"{{{_NS}}}infDPS" in child_tags
    assert f"{{{_DSIG}}}Signature" in child_tags


def test_sign_reference_uri_aponta_para_inf_dps(test_cert):
    pfx_path, _ = test_cert
    from app.integrations.betha.xml_signer import DpsXmlSigner

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    root = etree.fromstring(result.encode())
    ref = root.find(f".//{{{_DSIG}}}Reference")
    assert ref is not None
    assert ref.get("URI") == f"#{_INF_DPS_ID}"


def test_sign_key_info_apenas_x509_certificate(test_cert):
    pfx_path, _ = test_cert
    from app.integrations.betha.xml_signer import DpsXmlSigner

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    root = etree.fromstring(result.encode())
    assert root.find(f".//{{{_DSIG}}}X509Certificate") is not None
    assert root.find(f".//{{{_DSIG}}}X509SubjectName") is None
    assert root.find(f".//{{{_DSIG}}}KeyValue") is None
    assert root.find(f".//{{{_DSIG}}}Modulus") is None


def test_sign_verificacao_com_signxml(test_cert):
    pfx_path, cert = test_cert
    from app.integrations.betha.xml_signer import DpsXmlSigner
    from signxml import XMLVerifier  # type: ignore[import-untyped]

    with patch("app.integrations.betha.xml_signer.settings") as mock_settings:
        mock_settings.BETHA_CERT_PATH = pfx_path
        mock_settings.BETHA_CERT_PASSWORD = None
        result = DpsXmlSigner().sign(_SAMPLE_XML)

    # Deve passar sem levantar exceção
    XMLVerifier().verify(result.encode(), x509_cert=cert, id_attribute="id")

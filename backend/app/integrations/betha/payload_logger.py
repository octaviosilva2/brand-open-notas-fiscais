# app/integrations/betha/payload_logger.py
import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from app.core.settings import settings

logger = logging.getLogger(__name__)


def _ensure_dir(date_str: str) -> Path:
    path = Path(settings.BETHA_LOG_DIR) / date_str
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pretty_xml(xml_str: str) -> str:
    try:
        root = ET.fromstring(xml_str)
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode")
    except ET.ParseError:
        return xml_str


def _write_pair(
    log_dir: Path, ts: str, operation: str, request: str, response: str
) -> None:
    (log_dir / f"{ts}_{operation}_request.xml").write_text(
        _pretty_xml(request), encoding="utf-8"
    )
    (log_dir / f"{ts}_{operation}_response.xml").write_text(
        _pretty_xml(response), encoding="utf-8"
    )


async def log_betha_exchange(operation: str, request: str, response: str) -> None:
    """Grava em disco o par request/response de uma chamada à API da Betha."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H%M%S_%f")
    try:
        log_dir = await asyncio.to_thread(_ensure_dir, date_str)
        await asyncio.to_thread(_write_pair, log_dir, ts, operation, request, response)
    except Exception:
        logger.exception("Falha ao salvar log da Betha (operação=%s)", operation)

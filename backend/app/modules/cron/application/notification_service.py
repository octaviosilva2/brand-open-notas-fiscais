# app/modules/cron/application/notification_service.py
import logging
from dataclasses import dataclass
from datetime import date

from app.core.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class NotificationItem:
    client_name: str
    ok: bool
    nf_number: str | None = None
    pdf_url: str | None = None
    error_message: str | None = None


class NotificationService:
    async def send_summary(
        self,
        target_date: date,
        items: list[NotificationItem],
    ) -> None:
        """Envia e-mail de resumo. Se SMTP não configurado, apenas loga."""
        if not settings.SMTP_HOST:
            logger.warning("SMTP não configurado. Resumo de emissão não enviado.")
            return

        successes = [i for i in items if i.ok]
        errors = [i for i in items if not i.ok]
        subject = (
            f"NFS-e — Resumo de emissão: {target_date} "
            f"({len(successes)} sucesso, {len(errors)} erro)"
        )
        body = self._build_html(target_date, successes, errors)

        try:
            await self._send_email(subject, body)
        except Exception as exc:
            logger.error(f"Falha ao enviar e-mail de resumo: {exc}")

    def _build_html(
        self,
        target_date: date,
        successes: list[NotificationItem],
        errors: list[NotificationItem],
    ) -> str:
        lines = [
            f"<h2>Resumo da emissão do dia {target_date}</h2>",
            f"<p>✅ {len(successes)} nota(s) emitida(s) com sucesso</p>",
            f"<p>❌ {len(errors)} nota(s) com falha</p>",
        ]
        if successes:
            lines.append("<h3>Sucessos</h3><ul>")
            for item in successes:
                pdf_link = (
                    f' <a href="{item.pdf_url}">[PDF]</a>' if item.pdf_url else ""
                )
                lines.append(
                    f"<li>{item.client_name} — NF nº {item.nf_number}{pdf_link}</li>"
                )
            lines.append("</ul>")
        if errors:
            lines.append("<h3>Erros</h3><ul>")
            for item in errors:
                lines.append(f"<li>{item.client_name} — {item.error_message}</li>")
            lines.append("</ul>")
        lines.append(
            "<hr><p><small>"
            "Emissão realizada automaticamente pelo sistema Brand Open NFS-e."
            "</small></p>"
        )
        return "".join(lines)

    async def _send_email(self, subject: str, body: str) -> None:
        from email.message import EmailMessage

        import aiosmtplib

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.NOTIFICATION_FROM or settings.SMTP_USER or ""
        msg["To"] = settings.NOTIFICATION_EMAIL or ""
        msg.set_content(body, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
        )

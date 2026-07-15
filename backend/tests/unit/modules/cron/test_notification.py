# tests/unit/modules/cron/test_notification.py
from datetime import date
from unittest.mock import patch

from app.modules.cron.application.notification_service import (
    NotificationItem,
    NotificationService,
)


async def test_send_summary_no_smtp_logs_warning():
    service = NotificationService()
    with patch("app.modules.cron.application.notification_service.settings") as s:
        s.SMTP_HOST = None
        items = [NotificationItem(client_name="A", ok=True, nf_number="001")]
        await service.send_summary(date(2026, 6, 15), items)


async def test_build_html_contains_success_and_error():
    service = NotificationService()
    items_ok = [
        NotificationItem(
            client_name="A", ok=True, nf_number="NF001", pdf_url="http://pdf"
        )
    ]
    items_err = [NotificationItem(client_name="B", ok=False, error_message="Timeout")]
    html = service._build_html(date(2026, 6, 15), items_ok, items_err)
    assert "NF001" in html
    assert "Timeout" in html
    assert "✅" in html
    assert "❌" in html

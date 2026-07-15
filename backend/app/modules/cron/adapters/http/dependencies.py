# app/modules/cron/adapters/http/dependencies.py
from typing import Annotated

from fastapi import Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.settings import settings

bearer = HTTPBearer(auto_error=False)


async def validate_cron_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> None:
    """Aceita Bearer JWT (sessão normal) ou X-Cron-Secret (cron externo)."""
    # Tenta autenticar via Bearer JWT padrão
    if credentials:
        try:
            from app.core.security.access_tokens import decode_access_token

            decode_access_token(credentials.credentials)
            return
        except Exception:
            pass

    # Tenta autenticar via secret compartilhado para chamadas de cron externo
    secret = request.headers.get("X-Cron-Secret")
    if secret and settings.CRON_SECRET and secret == settings.CRON_SECRET:
        return

    raise UnauthorizedError("Autenticação inválida para o endpoint de cron.")

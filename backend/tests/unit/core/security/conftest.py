from collections.abc import Iterator
from unittest.mock import patch

import pytest

# Valores de teste para o JWT. O .env do projeto contém apenas placeholders
# inválidos (ex.: JWT_ALGORITHM="1"), então sobrescrevemos com valores reais
# para que jose consiga de fato codificar/decodificar tokens.
JWT_SECRET = "test-secret-key-for-unit-tests"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_MIN = 15
REFRESH_TOKEN_EXPIRES_DAYS = 7


@pytest.fixture(autouse=True)
def patch_security_settings() -> Iterator[None]:
    """Sobrescreve o `settings` usado pelos módulos de segurança.

    `create_token`/`decode_token` leem o `settings` do módulo `jwt`, enquanto
    os tempos de expiração são lidos do `settings` do módulo `access_tokens`.
    Ambos são corrigidos aqui para que os testes não dependam do `.env`.
    """

    with (
        patch("app.core.security.jwt.settings") as jwt_settings,
        patch("app.core.security.access_tokens.settings") as access_settings,
    ):
        jwt_settings.JWT_SECRET = JWT_SECRET
        jwt_settings.JWT_ALGORITHM = JWT_ALGORITHM
        access_settings.ACCESS_TOKEN_EXPIRES_MIN = ACCESS_TOKEN_EXPIRES_MIN
        access_settings.REFRESH_TOKEN_EXPIRES_DAYS = REFRESH_TOKEN_EXPIRES_DAYS
        yield

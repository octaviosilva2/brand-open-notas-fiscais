# app/integrations/betha/exceptions.py


class BethaError(Exception):
    """Erro retornado pela API Betha (código de erro no XML de resposta)."""


class BethaTimeoutError(BethaError):
    """Polling esgotou o número máximo de tentativas."""

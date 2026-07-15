from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    """Comando de aplicação para autenticar um usuário."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RefreshCommand:
    """Comando de aplicação para renovar o par de tokens."""

    refresh_token: str

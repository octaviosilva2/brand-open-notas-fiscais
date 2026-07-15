from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Corpo da requisição de login. `username` corresponde ao email do usuário."""

    username: str
    password: str


class RefreshRequest(BaseModel):
    """Corpo da requisição de renovação de tokens."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Par de tokens devolvido por login e refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

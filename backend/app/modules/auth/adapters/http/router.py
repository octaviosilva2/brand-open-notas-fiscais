from fastapi import APIRouter

from app.modules.auth.adapters.http.dependencies import AuthUnitOfWorkDep
from app.modules.auth.adapters.http.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.modules.auth.application.dtos.commands import LoginCommand, RefreshCommand
from app.modules.auth.application.use_cases.login import AuthLogin
from app.modules.auth.application.use_cases.refresh import AuthRefresher

# Rotas públicas: não aplicam autenticação (é aqui que os tokens são obtidos).
router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, uow: AuthUnitOfWorkDep) -> TokenResponse:
    """Autentica por email/senha e devolve um par de tokens."""
    pair = await AuthLogin(uow).login(
        LoginCommand(email=body.username, password=body.password)
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, uow: AuthUnitOfWorkDep) -> TokenResponse:
    """Renova o par de tokens a partir de um refresh token válido."""
    pair = await AuthRefresher(uow).refresh(
        RefreshCommand(refresh_token=body.refresh_token)
    )
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
    )

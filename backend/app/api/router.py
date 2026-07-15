from fastapi import APIRouter

from app.modules.auth.adapters.http.router import router as auth_router
from app.modules.clients.adapters.http.router import router as clients_router
from app.modules.cnpj.adapters.http.router import router as brasilapi_router
from app.modules.cron.adapters.http.router import router as cron_router
from app.modules.invoices.adapters.http.router import router as invoices_router
from app.modules.lookups.router import router as lookups_router
from app.modules.recurrences.adapters.http.router import router as recurrences_router
from app.modules.users.adapters.http.router import router as users_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
    router.include_router(users_router, prefix="/users", tags=["Usuários"])
    router.include_router(clients_router, prefix="/clients", tags=["Clientes"])
    router.include_router(
        recurrences_router, prefix="/recurrences", tags=["Recorrências"]
    )
    router.include_router(invoices_router, prefix="/invoices", tags=["Invoices"])
    router.include_router(lookups_router, prefix="/lookups", tags=["Lookups"])
    router.include_router(cron_router, prefix="/cron", tags=["Cron"])
    router.include_router(brasilapi_router, prefix="/cnpj", tags=["BrasilAPI"])
    return router


api_router = build_api_router()

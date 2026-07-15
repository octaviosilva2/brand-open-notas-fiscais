# app/modules/lookups/router.py
from fastapi import APIRouter, Depends, Query

from app.modules.lookups.schemas import LookupOption
from app.modules.lookups.service import search
from app.modules.users.adapters.http.dependencies import get_current_actor

router = APIRouter(dependencies=[Depends(get_current_actor)])


@router.get("/municipios", response_model=list[LookupOption])
async def list_municipios(
    q: str = Query("", description="Texto de busca"),
    limit: int = Query(50, ge=1, le=200),
) -> list[LookupOption]:
    return search("municipios", q, limit)


@router.get("/paises", response_model=list[LookupOption])
async def list_paises(
    q: str = Query("", description="Texto de busca"),
    limit: int = Query(50, ge=1, le=200),
) -> list[LookupOption]:
    return search("paises", q, limit)


@router.get("/servicos", response_model=list[LookupOption])
async def list_servicos(
    q: str = Query("", description="Texto de busca"),
    limit: int = Query(50, ge=1, le=200),
) -> list[LookupOption]:
    return search("servicos", q, limit)


@router.get("/nbs", response_model=list[LookupOption])
async def list_nbs(
    q: str = Query("", description="Texto de busca"),
    limit: int = Query(50, ge=1, le=200),
) -> list[LookupOption]:
    return search("nbs", q, limit)

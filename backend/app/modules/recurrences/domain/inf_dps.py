# app/modules/recurrences/domain/inf_dps.py
"""Contrato `InfDps` — molde de DPS compartilhado.

Espelha a saída de `frontend/src/payload/buildInfDps.ts`. Todos os grupos são
opcionais; a omissão é controlada por `model_dump(exclude_none=True)` na hora de
serializar para o JSONB. Não inclui `prest` (fixo em settings) nem o cabeçalho
(`dCompet`, `serie`, `nDPS`, etc.), que são injetados na emissão.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Pessoa(_Base):
    """Tomador/Intermediário — só o ramo de documento escolhido pelo front vem."""

    CNPJ: str | None = None
    CPF: str | None = None
    NIF: str | None = None
    cNaoNIF: str | None = None
    IM: str | None = None
    CAEPF: str | None = None
    xNome: str | None = None
    fone: str | None = None
    email: str | None = None
    # endNac/endExt já montado pelo front: {endNac|endExt: {...}, xLgr, nro, ...}
    end: dict[str, Any] | None = None


class CServ(_Base):
    cTribNac: str | None = None
    cTribMun: str | None = None
    cNBS: str | None = None
    cIntContrib: str | None = None
    xDescServ: str | None = None


class Serv(_Base):
    locPrest: dict[str, Any] | None = None  # {cLocPrestacao} ou {cPaisPrestacao}
    cServ: CServ | None = None
    obra: dict[str, Any] | None = None
    atvEvento: dict[str, Any] | None = None
    infoCompl: dict[str, Any] | None = None


class Valores(_Base):
    vServPrest: dict[str, Any] | None = None
    vDescCondIncond: dict[str, Any] | None = None
    vDedRed: dict[str, Any] | None = None
    trib: dict[str, Any] | None = None  # tribMun/tribFed


class InfDps(_Base):
    tpEmit: str | None = None  # default "1" aplicado na emissão se ausente
    regEspTrib: str | None = None  # sobrescreve settings.REG_ESP_TRIB se presente
    toma: Pessoa | None = None
    interm: Pessoa | None = None
    serv: Serv | None = None
    valores: Valores | None = None

# app/modules/lookups/service.py
import json
from functools import cache
from importlib.resources import files

from app.modules.lookups.schemas import LookupOption

_DATASETS = ("municipios", "paises", "servicos", "nbs")


@cache
def _load(dataset: str) -> tuple[LookupOption, ...]:
    raw = (
        files("app.modules.lookups.data").joinpath(f"{dataset}.json").read_text("utf-8")
    )
    return tuple(LookupOption(**item) for item in json.loads(raw))


def search(dataset: str, query: str, limit: int = 50) -> list[LookupOption]:
    """Busca por substring em `label` ou prefixo em `value` (case-insensitive).

    Sem `query`, retorna os primeiros `limit` itens.
    """
    options = _load(dataset)
    q = query.strip().lower()
    if not q:
        return list(options[:limit])
    result = [
        opt
        for opt in options
        if q in opt.label.lower() or opt.value.lower().startswith(q)
    ]
    return result[:limit]

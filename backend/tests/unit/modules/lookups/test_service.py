from app.modules.lookups.service import search


def test_busca_por_label() -> None:
    res = search("municipios", "jaraguá")
    assert any(o.value == "4208906" for o in res)


def test_busca_por_prefixo_value() -> None:
    res = search("paises", "BR")
    assert res and res[0].value == "BRA"


def test_query_vazia_respeita_limit() -> None:
    assert len(search("servicos", "", limit=2)) <= 2


def test_case_insensitive() -> None:
    # busca é case-insensitive (mas não ignora acento)
    assert search("municipios", "JARAGUÁ") == search("municipios", "jaraguá")
    assert any(o.value == "4208906" for o in search("municipios", "jaraguá"))


def test_busca_por_label_substring() -> None:
    res = search("nbs", "consultoria")
    assert res
    assert all("consultoria" in o.label.lower() for o in res)

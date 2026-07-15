from app.modules.cnpj.domain.entities import CnpjInfo

_FULL = CnpjInfo(
    name="Empresa Exemplo Ltda",
    phone="11999990000",
    email="empresa@exemplo.com",
    zip_code="01310100",
    street="Av. Paulista",
    number="1000",
    complement="Sala 1",
    neighborhood="Bela Vista",
    ibge_city_code="3550308",
)

_EMPTY = CnpjInfo(
    name=None,
    phone=None,
    email=None,
    zip_code=None,
    street=None,
    number=None,
    complement=None,
    neighborhood=None,
    ibge_city_code=None,
)

_EXPECTED_KEYS = {
    "name",
    "phone",
    "email",
    "zip_code",
    "street",
    "number",
    "complement",
    "neighborhood",
    "ibge_city_code",
}


class TestCnpjInfoToDict:
    def test_to_dict_returns_all_nine_keys(self) -> None:
        result = _FULL.to_dict()
        assert set(result.keys()) == _EXPECTED_KEYS

    def test_to_dict_maps_values_correctly(self) -> None:
        result = _FULL.to_dict()
        assert result["name"] == "Empresa Exemplo Ltda"
        assert result["phone"] == "11999990000"
        assert result["email"] == "empresa@exemplo.com"
        assert result["zip_code"] == "01310100"
        assert result["street"] == "Av. Paulista"
        assert result["number"] == "1000"
        assert result["complement"] == "Sala 1"
        assert result["neighborhood"] == "Bela Vista"
        assert result["ibge_city_code"] == "3550308"

    def test_to_dict_with_all_none_fields_still_returns_all_keys(self) -> None:
        result = _EMPTY.to_dict()
        assert set(result.keys()) == _EXPECTED_KEYS
        assert all(v is None for v in result.values())

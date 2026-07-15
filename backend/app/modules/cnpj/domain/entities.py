from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CnpjInfo:
    name: str | None
    phone: str | None
    email: str | None
    zip_code: str | None
    street: str | None
    number: str | None
    complement: str | None
    neighborhood: str | None
    ibge_city_code: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "zip_code": self.zip_code,
            "street": self.street,
            "number": self.number,
            "complement": self.complement,
            "neighborhood": self.neighborhood,
            "ibge_city_code": self.ibge_city_code,
        }

from typing import Annotated

from pydantic import BaseModel, Field

Name = Annotated[str, Field(..., description="O nome da empresa associada ao CNPJ.")]

Phone = Annotated[
    str | None,
    Field(default=None, description="O telefone de contato da empresa."),
]

Email = Annotated[
    str | None,
    Field(default=None, description="O email de contato da empresa."),
]

ZipCode = Annotated[
    str | None,
    Field(default=None, description="O CEP da empresa associada ao CNPJ."),
]

Street = Annotated[
    str | None,
    Field(default=None, description="O logradouro da empresa associada ao CNPJ."),
]

Number = Annotated[
    str | None,
    Field(default=None, description="O número do endereço da empresa."),
]

Complement = Annotated[
    str | None,
    Field(default=None, description="O complemento do endereço da empresa."),
]

Neighborhood = Annotated[
    str | None,
    Field(default=None, description="O bairro da empresa associada ao CNPJ."),
]

IbgeCityCode = Annotated[
    str | None,
    Field(default=None, description="O código IBGE da cidade da empresa."),
]


class CnpjInfoResponse(BaseModel):
    name: Name
    phone: Phone = None
    email: Email = None
    zip_code: ZipCode = None
    street: Street = None
    number: Number = None
    complement: Complement = None
    neighborhood: Neighborhood = None
    ibge_city_code: IbgeCityCode = None

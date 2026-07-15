import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Credentials:
    """Credenciais de um usuário usadas para autenticação.

    Lida da tabela de usuários apenas com os campos necessários para login e
    revalidação de token — nunca expostos fora do módulo `auth`.
    """

    id: uuid.UUID
    password_hash: str
    is_active: bool

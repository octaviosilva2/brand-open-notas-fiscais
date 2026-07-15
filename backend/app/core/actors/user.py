import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserActor:
    user_id: uuid.UUID

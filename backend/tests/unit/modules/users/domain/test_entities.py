import uuid
from datetime import datetime

from app.modules.users.domain.entities import User


class TestUserToDict:
    def _user(self) -> User:
        now = datetime(2026, 6, 11, 12, 0, 0)
        return User(
            id=uuid.uuid4(),
            email="user@example.com",
            name="Fulano",
            phone="11999999999",
            is_active=True,
            updated_at=now,
            created_at=now,
        )

    def test_includes_phone(self):
        user = self._user()

        assert user.to_dict()["phone"] == "11999999999"

    def test_keys_have_no_trailing_whitespace(self):
        user = self._user()

        data = user.to_dict()

        assert all(key == key.strip() for key in data)

    def test_exposes_all_entity_fields(self):
        user = self._user()

        data = user.to_dict()

        assert set(data) == {
            "id",
            "email",
            "name",
            "phone",
            "is_active",
            "updated_at",
            "created_at",
        }

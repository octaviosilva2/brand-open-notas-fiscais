import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.modules.users.adapters.http.schemas import (
    ChangePassword,
    UserCreate,
    UserRead,
    UsersPaginationFilters,
    UserUpdate,
)


def make_user_read_data(**overrides: object) -> dict:
    now = datetime(2026, 6, 11, 12, 0, 0)
    data = {
        "id": uuid.uuid7(),
        "name": "Fulano de Tal",
        "email": "fulano@example.com",
        "phone": "11999999999",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    data.update(overrides)
    return data


class TestUserCreate:
    def test_accepts_valid_data(self):
        user = UserCreate(
            name="Fulano",
            email="fulano@example.com",
            phone="11999999999",
            password="senha1234",
        )

        assert user.name == "Fulano"
        assert user.email == "fulano@example.com"
        assert user.phone == "11999999999"
        assert user.password == "senha1234"

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                email="not-an-email",
                phone="11999999999",
                password="senha1234",
            )

    def test_rejects_password_shorter_than_8_chars(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                email="fulano@example.com",
                phone="11999999999",
                password="curta",
            )

    def test_accepts_password_exactly_8_chars(self):
        user = UserCreate(
            name="Fulano",
            email="fulano@example.com",
            phone="11999999999",
            password="12345678",
        )

        assert len(user.password) == 8

    def test_rejects_name_longer_than_255_chars(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="A" * 256,
                email="fulano@example.com",
                phone="11999999999",
                password="senha1234",
            )

    def test_rejects_phone_longer_than_20_chars(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                email="fulano@example.com",
                phone="0" * 21,
                password="senha1234",
            )

    def test_requires_name(self):
        with pytest.raises(ValidationError):
            UserCreate(
                email="fulano@example.com",
                phone="11999999999",
                password="senha1234",
            )

    def test_requires_email(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                phone="11999999999",
                password="senha1234",
            )

    def test_requires_phone(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                email="fulano@example.com",
                password="senha1234",
            )

    def test_requires_password(self):
        with pytest.raises(ValidationError):
            UserCreate(
                name="Fulano",
                email="fulano@example.com",
                phone="11999999999",
            )


class TestUserRead:
    def test_accepts_valid_data(self):
        data = make_user_read_data()
        user = UserRead(**data)

        assert user.name == "Fulano de Tal"
        assert user.email == "fulano@example.com"
        assert user.is_active is True

    def test_model_validate_from_dict(self):
        data = make_user_read_data()

        user = UserRead.model_validate(data)

        assert user.id == data["id"]

    def test_id_is_uuid(self):
        data = make_user_read_data()
        user = UserRead(**data)

        assert isinstance(user.id, uuid.UUID)

    def test_has_created_at(self):
        now = datetime(2026, 6, 11, 12, 0, 0)
        data = make_user_read_data(created_at=now)
        user = UserRead(**data)

        assert user.created_at == now

    def test_has_updated_at(self):
        now = datetime(2026, 6, 11, 12, 0, 0)
        data = make_user_read_data(updated_at=now)
        user = UserRead(**data)

        assert user.updated_at == now

    def test_requires_id(self):
        data = make_user_read_data()
        data.pop("id")

        with pytest.raises(ValidationError):
            UserRead(**data)

    def test_requires_is_active(self):
        data = make_user_read_data()
        data.pop("is_active")

        with pytest.raises(ValidationError):
            UserRead(**data)


class TestUserUpdate:
    def test_all_fields_optional(self):
        user = UserUpdate()

        assert user.name is None
        assert user.email is None
        assert user.phone is None

    def test_accepts_partial_update_name_only(self):
        user = UserUpdate(name="Novo Nome")

        assert user.name == "Novo Nome"
        assert user.email is None
        assert user.phone is None

    def test_accepts_partial_update_email_only(self):
        user = UserUpdate(email="novo@example.com")

        assert user.email == "novo@example.com"

    def test_accepts_partial_update_phone_only(self):
        user = UserUpdate(phone="21988887777")

        assert user.phone == "21988887777"

    def test_rejects_invalid_email_when_provided(self):
        with pytest.raises(ValidationError):
            UserUpdate(email="not-valid")

    def test_rejects_name_exceeding_max_length(self):
        with pytest.raises(ValidationError):
            UserUpdate(name="A" * 256)

    def test_rejects_phone_exceeding_max_length(self):
        with pytest.raises(ValidationError):
            UserUpdate(phone="0" * 21)

    def test_accepts_all_fields(self):
        user = UserUpdate(
            name="Novo",
            email="novo@example.com",
            phone="21999998888",
        )

        assert user.name == "Novo"
        assert user.email == "novo@example.com"
        assert user.phone == "21999998888"


class TestChangePassword:
    def test_accepts_valid_passwords(self):
        cp = ChangePassword(current_password="senhaatual", password="novaSenha1")

        assert cp.current_password == "senhaatual"
        assert cp.password == "novaSenha1"

    def test_rejects_current_password_shorter_than_8(self):
        with pytest.raises(ValidationError):
            ChangePassword(current_password="curta", password="novaSenha1")

    def test_rejects_new_password_shorter_than_8(self):
        with pytest.raises(ValidationError):
            ChangePassword(current_password="senhaatual", password="curta")

    def test_accepts_passwords_exactly_8_chars(self):
        cp = ChangePassword(current_password="12345678", password="87654321")

        assert len(cp.current_password) == 8
        assert len(cp.password) == 8

    def test_requires_current_password(self):
        with pytest.raises(ValidationError):
            ChangePassword(password="novaSenha1")

    def test_requires_new_password(self):
        with pytest.raises(ValidationError):
            ChangePassword(current_password="senhaatual")


class TestUsersPaginationFilters:
    def test_defaults_both_fields_to_none(self):
        filters = UsersPaginationFilters()

        assert filters.q is None
        assert filters.is_active is None

    def test_accepts_q(self):
        filters = UsersPaginationFilters(q="fulano")

        assert filters.q == "fulano"

    def test_accepts_is_active_true(self):
        filters = UsersPaginationFilters(is_active=True)

        assert filters.is_active is True

    def test_accepts_is_active_false(self):
        filters = UsersPaginationFilters(is_active=False)

        assert filters.is_active is False

    def test_accepts_both_fields(self):
        filters = UsersPaginationFilters(q="admin", is_active=True)

        assert filters.q == "admin"
        assert filters.is_active is True

    def test_accepts_explicit_none_for_both(self):
        filters = UsersPaginationFilters(q=None, is_active=None)

        assert filters.q is None
        assert filters.is_active is None

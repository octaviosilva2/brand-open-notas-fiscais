import pytest

from app.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationAppError,
)


class TestAppError:
    def test_is_exception_subclass(self):
        assert issubclass(AppError, Exception)

    def test_default_status_code(self):
        assert AppError.status_code == 400

    def test_default_code(self):
        assert AppError.code == "app_error"

    def test_default_message_when_none_passed(self):
        error = AppError()

        assert error.message == "An application error occurred."

    def test_custom_message_overrides_default(self):
        error = AppError("Custom message.")

        assert error.message == "Custom message."

    def test_exception_args_contain_message(self):
        error = AppError("Custom message.")

        assert str(error) == "Custom message."

    def test_exception_args_use_default_when_no_message(self):
        error = AppError()

        assert str(error) == "An application error occurred."

    def test_details_is_none_by_default(self):
        error = AppError()

        assert error.details is None

    def test_accepts_dict_details(self):
        details = {"field": "value"}
        error = AppError(details=details)

        assert error.details == details

    def test_accepts_list_of_dicts_details(self):
        details = [{"field": "a"}, {"field": "b"}]
        error = AppError(details=details)

        assert error.details == details

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AppError):
            raise AppError("erro")

    def test_can_be_caught_as_exception(self):
        with pytest.raises(AppError):
            raise AppError("erro")


class TestNotFoundError:
    def test_is_app_error_subclass(self):
        assert issubclass(NotFoundError, AppError)

    def test_status_code(self):
        assert NotFoundError.status_code == 404

    def test_code(self):
        assert NotFoundError.code == "not_found"

    def test_default_message(self):
        error = NotFoundError()

        assert error.message == "Resource not found."

    def test_accepts_custom_message(self):
        error = NotFoundError("Item não encontrado.")

        assert error.message == "Item não encontrado."

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise NotFoundError()


class TestConflictError:
    def test_is_app_error_subclass(self):
        assert issubclass(ConflictError, AppError)

    def test_status_code(self):
        assert ConflictError.status_code == 409

    def test_code(self):
        assert ConflictError.code == "conflict"

    def test_default_message(self):
        error = ConflictError()

        assert error.message == "Resource conflict."

    def test_accepts_custom_message(self):
        error = ConflictError("Email já cadastrado.")

        assert error.message == "Email já cadastrado."

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise ConflictError()


class TestUnauthorizedError:
    def test_is_app_error_subclass(self):
        assert issubclass(UnauthorizedError, AppError)

    def test_status_code(self):
        assert UnauthorizedError.status_code == 401

    def test_code(self):
        assert UnauthorizedError.code == "unauthorized"

    def test_default_message(self):
        error = UnauthorizedError()

        assert error.message == "Invalid credentials."

    def test_accepts_custom_message(self):
        error = UnauthorizedError("Token expirado.")

        assert error.message == "Token expirado."

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise UnauthorizedError()


class TestForbiddenError:
    def test_is_app_error_subclass(self):
        assert issubclass(ForbiddenError, AppError)

    def test_status_code(self):
        assert ForbiddenError.status_code == 403

    def test_code(self):
        assert ForbiddenError.code == "forbidden"

    def test_default_message(self):
        error = ForbiddenError()

        assert error.message == "You do not have permission to perform this action."

    def test_accepts_custom_message(self):
        error = ForbiddenError("Acesso negado.")

        assert error.message == "Acesso negado."

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise ForbiddenError()


class TestValidationAppError:
    def test_is_app_error_subclass(self):
        assert issubclass(ValidationAppError, AppError)

    def test_status_code(self):
        assert ValidationAppError.status_code == 422

    def test_code(self):
        assert ValidationAppError.code == "validation_error"

    def test_default_message(self):
        error = ValidationAppError()

        assert error.message == "Validation error."

    def test_accepts_custom_message(self):
        error = ValidationAppError("Campo obrigatório ausente.")

        assert error.message == "Campo obrigatório ausente."

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise ValidationAppError()

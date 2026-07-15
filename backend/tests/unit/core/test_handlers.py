import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.handlers import register_exception_handlers


def make_app(*raises: AppError) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/error")
    async def trigger_error():
        raise raises[0]

    return app


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    return app


async def _get(app: FastAPI, path: str = "/error"):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(path)


class TestRegisterExceptionHandlers:
    def test_registers_handler_for_app_error(self, app: FastAPI):
        assert AppError in app.exception_handlers


class TestHandleAppError:
    async def test_returns_json_response(self):
        error = AppError("Algo deu errado.")
        app = make_app(error)

        response = await _get(app)

        assert response.headers["content-type"].startswith("application/json")

    async def test_status_code_from_exception(self):
        error = AppError("erro")
        app = make_app(error)

        response = await _get(app)

        assert response.status_code == 400

    async def test_body_contains_code(self):
        error = AppError("erro")
        app = make_app(error)

        response = await _get(app)

        assert response.json()["code"] == "app_error"

    async def test_body_contains_message(self):
        error = AppError("Mensagem de teste.")
        app = make_app(error)

        response = await _get(app)

        assert response.json()["message"] == "Mensagem de teste."

    async def test_body_contains_details(self):
        error = AppError("erro", details={"field": "name"})
        app = make_app(error)

        response = await _get(app)

        assert response.json()["details"] == {"field": "name"}

    async def test_details_is_null_when_none(self):
        error = AppError("erro")
        app = make_app(error)

        response = await _get(app)

        assert response.json()["details"] is None

    async def test_not_found_error_returns_404(self):
        app = make_app(NotFoundError())

        response = await _get(app)

        assert response.status_code == 404

    async def test_not_found_error_code(self):
        app = make_app(NotFoundError())

        response = await _get(app)

        assert response.json()["code"] == "not_found"

    async def test_conflict_error_returns_409(self):
        app = make_app(ConflictError())

        response = await _get(app)

        assert response.status_code == 409

    async def test_forbidden_error_returns_403(self):
        app = make_app(ForbiddenError())

        response = await _get(app)

        assert response.status_code == 403

    async def test_subclass_message_is_used(self):
        app = make_app(NotFoundError("Usuário não encontrado."))

        response = await _get(app)

        assert response.json()["message"] == "Usuário não encontrado."

    async def test_details_list_is_serialized(self):
        details = [{"field": "email"}, {"field": "name"}]
        app = make_app(AppError("erro", details=details))

        response = await _get(app)

        assert response.json()["details"] == details

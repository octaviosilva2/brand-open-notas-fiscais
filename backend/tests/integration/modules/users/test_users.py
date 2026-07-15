import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from tests.integration.modules.users.conftest import insert_user


class TestGetMe:
    async def test_retorna_usuario_autenticado(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user)
        assert data["email"] == "integracao@test.com"
        assert data["is_active"] is True

    async def test_sem_token_retorna_401(self, client: AsyncClient):
        response = await client.get("/users/me")

        assert response.status_code == 401


class TestUpdateMe:
    async def test_atualiza_usuario_autenticado(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.patch(
            "/users/me",
            json={"name": "Nome Atualizado"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Nome Atualizado"
        assert data["id"] == str(test_user)


class TestPaginateUsers:
    async def test_retorna_lista_paginada(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.get("/users", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "total" in body
        assert body["total"] >= 1

    async def test_filtro_is_active_true(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.get("/users?is_active=true", headers=auth_headers)

        assert response.status_code == 200
        items = response.json()["data"]
        assert all(u["is_active"] for u in items)

    async def test_filtro_is_active_false(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        await insert_user(
            db_connection,
            email="inativo@test.com",
            phone="11988880002",
            is_active=False,
        )

        response = await client.get("/users?is_active=false", headers=auth_headers)

        assert response.status_code == 200
        items = response.json()["data"]
        assert all(not u["is_active"] for u in items)


class TestGetUser:
    async def test_retorna_usuario_por_id(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.get(f"/users/{test_user}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user)
        assert data["email"] == "integracao@test.com"

    async def test_id_inexistente_retorna_404(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        unknown_id = uuid.uuid4()
        response = await client.get(f"/users/{unknown_id}", headers=auth_headers)

        assert response.status_code == 404


class TestCreateUser:
    async def test_cria_usuario(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        payload = {
            "name": "Novo Usuário",
            "email": "novo@test.com",
            "phone": "11977770001",
            "password": "senha5678",
        }

        response = await client.post("/users", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "novo@test.com"
        assert data["name"] == "Novo Usuário"
        assert data["is_active"] is True
        assert "id" in data

    async def test_email_duplicado_retorna_409(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        payload = {
            "name": "Duplicado",
            "email": "integracao@test.com",
            "phone": "11966660001",
            "password": "senha5678",
        }

        response = await client.post("/users", json=payload, headers=auth_headers)

        assert response.status_code == 409


class TestUpdateUser:
    async def test_atualiza_usuario_por_id(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        response = await client.patch(
            f"/users/{test_user}",
            json={"name": "Nome via Admin"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Nome via Admin"


class TestDeleteUser:
    async def test_deleta_usuario(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        other_id = await insert_user(
            db_connection,
            email="deletar@test.com",
            phone="11955550001",
        )

        response = await client.delete(f"/users/{other_id}", headers=auth_headers)

        assert response.status_code == 204

    async def test_id_inexistente_retorna_404(
        self,
        client: AsyncClient,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        unknown_id = uuid.uuid4()
        response = await client.delete(f"/users/{unknown_id}", headers=auth_headers)

        assert response.status_code == 404


class TestActivateUser:
    async def test_ativa_usuario_inativo(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        inactive_id = await insert_user(
            db_connection,
            email="inativo2@test.com",
            phone="11944440001",
            is_active=False,
        )

        response = await client.post(
            f"/users/{inactive_id}/activate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is True


class TestDeactivateUser:
    async def test_desativa_usuario_ativo(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
        test_user: uuid.UUID,
        auth_headers: dict,
    ):
        other_id = await insert_user(
            db_connection,
            email="desativar@test.com",
            phone="11933330001",
        )

        response = await client.post(
            f"/users/{other_id}/deactivate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

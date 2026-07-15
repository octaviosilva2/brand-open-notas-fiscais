import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
)
from tests.integration.modules.auth.conftest import LOGIN_EMAIL, LOGIN_PASSWORD
from tests.integration.modules.users.conftest import insert_user


class TestLogin:
    async def test_login_sucesso(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        response = await client.post(
            "/auth/login",
            json={"username": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"

    async def test_senha_errada_retorna_401(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        response = await client.post(
            "/auth/login",
            json={"username": LOGIN_EMAIL, "password": "senha-errada"},
        )

        assert response.status_code == 401

    async def test_email_inexistente_retorna_401(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={"username": "naoexiste@test.com", "password": "qualquer"},
        )

        assert response.status_code == 401

    async def test_usuario_inativo_retorna_401(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
    ):
        await insert_user(
            db_connection,
            email="inativo@test.com",
            phone="11990002222",
            password=LOGIN_PASSWORD,
            is_active=False,
        )

        response = await client.post(
            "/auth/login",
            json={"username": "inativo@test.com", "password": LOGIN_PASSWORD},
        )

        assert response.status_code == 401

    async def test_access_token_autentica_em_users_me(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        login = await client.post(
            "/auth/login",
            json={"username": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        )
        token = login.json()["access_token"]

        me = await client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

        assert me.status_code == 200
        assert me.json()["id"] == str(login_user)


class TestRefresh:
    async def test_refresh_sucesso(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        login = await client.post(
            "/auth/login",
            json={"username": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        )
        refresh_token = login.json()["refresh_token"]

        response = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"

    async def test_novo_access_token_autentica_em_users_me(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        login = await client.post(
            "/auth/login",
            json={"username": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
        )
        refresh_token = login.json()["refresh_token"]

        refreshed = await client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        new_access = refreshed.json()["access_token"]

        me = await client.get(
            "/users/me", headers={"Authorization": f"Bearer {new_access}"}
        )

        assert me.status_code == 200
        assert me.json()["id"] == str(login_user)

    async def test_token_invalido_retorna_401(self, client: AsyncClient):
        response = await client.post(
            "/auth/refresh", json={"refresh_token": "not-a-jwt"}
        )

        assert response.status_code == 401

    async def test_access_token_como_refresh_retorna_401(
        self,
        client: AsyncClient,
        login_user: uuid.UUID,
    ):
        access = create_access_token(TokenIdentity(subject=login_user))

        response = await client.post("/auth/refresh", json={"refresh_token": access})

        assert response.status_code == 401

    async def test_usuario_inativo_retorna_401(
        self,
        client: AsyncClient,
        db_connection: AsyncConnection,
    ):
        uid = await insert_user(
            db_connection,
            email="inativo-refresh@test.com",
            phone="11990003333",
            is_active=False,
        )
        token = create_refresh_token(TokenIdentity(subject=uid))

        response = await client.post("/auth/refresh", json={"refresh_token": token})

        assert response.status_code == 401

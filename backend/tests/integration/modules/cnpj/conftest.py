from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.integrations.brasilapi.client import BrasilApiClient


@pytest.fixture
def brasilapi_mock() -> AsyncMock:
    return AsyncMock(spec=BrasilApiClient)


@pytest.fixture
async def client(brasilapi_mock: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.modules.cnpj.adapters.http.depencencies import get_brasilapi_client

    app.dependency_overrides[get_brasilapi_client] = lambda: brasilapi_mock
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()

import uuid
from unittest.mock import patch

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.core.exceptions import UnauthorizedError
from app.core.security.dependencies import get_current_subject


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestGetCurrentSubject:
    async def test_returns_subject_uuid_from_claims(self):
        subject = uuid.uuid7()

        with patch("app.core.security.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"sub": str(subject), "type": "access"}

            result = await get_current_subject(make_credentials("a-token"))

        assert result == subject

    async def test_decodes_the_provided_credentials(self):
        with patch("app.core.security.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"sub": str(uuid.uuid7())}

            await get_current_subject(make_credentials("the-token"))

        mock_decode.assert_called_once_with("the-token")

    async def test_returns_uuid_instance(self):
        with patch("app.core.security.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"sub": str(uuid.uuid7())}

            result = await get_current_subject(make_credentials("a-token"))

        assert isinstance(result, uuid.UUID)

    async def test_propagates_unauthorized_from_decode(self):
        with patch("app.core.security.dependencies.decode_access_token") as mock_decode:
            mock_decode.side_effect = UnauthorizedError("Invalid token.")

            with pytest.raises(UnauthorizedError, match="Invalid token"):
                await get_current_subject(make_credentials("bad-token"))

    async def test_raises_when_subject_is_not_a_valid_uuid(self):
        with patch("app.core.security.dependencies.decode_access_token") as mock_decode:
            mock_decode.return_value = {"sub": "not-a-uuid", "type": "access"}

            with pytest.raises(ValueError):
                await get_current_subject(make_credentials("a-token"))

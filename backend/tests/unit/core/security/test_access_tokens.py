import dataclasses
import uuid

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security.access_tokens import (
    TokenIdentity,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.core.security.jwt import create_token, decode_token
from tests.unit.core.security.conftest import (
    ACCESS_TOKEN_EXPIRES_MIN,
    REFRESH_TOKEN_EXPIRES_DAYS,
)


@pytest.fixture
def identity() -> TokenIdentity:
    return TokenIdentity(subject=uuid.uuid7())


class TestTokenIdentity:
    def test_stores_subject(self):
        subject = uuid.uuid7()

        identity = TokenIdentity(subject=subject)

        assert identity.subject == subject

    def test_is_frozen(self):
        identity = TokenIdentity(subject=uuid.uuid7())

        with pytest.raises(dataclasses.FrozenInstanceError):
            identity.subject = uuid.uuid7()  # type: ignore[misc]

    def test_equality_by_value(self):
        subject = uuid.uuid7()

        assert TokenIdentity(subject=subject) == TokenIdentity(subject=subject)


class TestCreateAccessToken:
    def test_returns_string(self, identity: TokenIdentity):
        assert isinstance(create_access_token(identity), str)

    def test_subject_matches_identity(self, identity: TokenIdentity):
        token = create_access_token(identity)

        claims = decode_token(token)

        assert claims["sub"] == str(identity.subject)

    def test_type_is_access(self, identity: TokenIdentity):
        token = create_access_token(identity)

        assert decode_token(token)["type"] == "access"

    def test_includes_iat_and_exp(self, identity: TokenIdentity):
        token = create_access_token(identity)

        claims = decode_token(token)

        assert "iat" in claims
        assert "exp" in claims

    def test_expires_after_configured_minutes(self, identity: TokenIdentity):
        token = create_access_token(identity)

        claims = decode_token(token)

        assert claims["exp"] - claims["iat"] == ACCESS_TOKEN_EXPIRES_MIN * 60


class TestCreateRefreshToken:
    def test_returns_string(self, identity: TokenIdentity):
        assert isinstance(create_refresh_token(identity), str)

    def test_subject_matches_identity(self, identity: TokenIdentity):
        token = create_refresh_token(identity)

        assert decode_token(token)["sub"] == str(identity.subject)

    def test_type_is_refresh(self, identity: TokenIdentity):
        token = create_refresh_token(identity)

        assert decode_token(token)["type"] == "refresh"

    def test_expires_after_configured_days(self, identity: TokenIdentity):
        token = create_refresh_token(identity)

        claims = decode_token(token)

        assert claims["exp"] - claims["iat"] == REFRESH_TOKEN_EXPIRES_DAYS * 86400


class TestDecodeAccessToken:
    def test_decodes_valid_access_token(self, identity: TokenIdentity):
        token = create_access_token(identity)

        claims = decode_access_token(token)

        assert claims["sub"] == str(identity.subject)
        assert claims["type"] == "access"

    def test_rejects_refresh_token(self, identity: TokenIdentity):
        token = create_refresh_token(identity)

        with pytest.raises(UnauthorizedError, match="Invalid token type refresh"):
            decode_access_token(token)

    def test_rejects_token_without_type(self, identity: TokenIdentity):
        token = create_token({"sub": str(identity.subject)})

        with pytest.raises(UnauthorizedError, match="Invalid token type None"):
            decode_access_token(token)

    def test_propagates_unauthorized_for_invalid_token(self):
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_access_token("not-a-jwt")


class TestDecodeRefreshToken:
    def test_decodes_valid_refresh_token(self, identity: TokenIdentity):
        token = create_refresh_token(identity)

        claims = decode_refresh_token(token)

        assert claims["sub"] == str(identity.subject)
        assert claims["type"] == "refresh"

    def test_rejects_access_token(self, identity: TokenIdentity):
        token = create_access_token(identity)

        with pytest.raises(UnauthorizedError, match="Invalid token type access"):
            decode_refresh_token(token)

    def test_rejects_token_without_type(self, identity: TokenIdentity):
        token = create_token({"sub": str(identity.subject)})

        with pytest.raises(UnauthorizedError, match="Invalid token type None"):
            decode_refresh_token(token)

    def test_propagates_unauthorized_for_invalid_token(self):
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_refresh_token("not-a-jwt")

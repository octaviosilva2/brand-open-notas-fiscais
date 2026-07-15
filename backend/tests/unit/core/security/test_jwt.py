from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt as jose_jwt

from app.core.exceptions import UnauthorizedError
from app.core.security.jwt import create_token, decode_token
from tests.unit.core.security.conftest import JWT_ALGORITHM, JWT_SECRET


class TestCreateToken:
    def test_returns_string(self):
        token = create_token({"sub": "user-123"})

        assert isinstance(token, str)

    def test_token_is_decodable_with_configured_key_and_algorithm(self):
        token = create_token({"sub": "user-123", "role": "admin"})

        decoded = jose_jwt.decode(
            token,
            key=JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        assert decoded["sub"] == "user-123"
        assert decoded["role"] == "admin"

    def test_accepts_any_mapping_of_claims(self):
        token = create_token({"a": 1, "b": "two", "c": True})

        decoded = jose_jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])

        assert decoded["a"] == 1
        assert decoded["b"] == "two"
        assert decoded["c"] is True

    def test_empty_claims_produces_valid_token(self):
        token = create_token({})

        decoded = jose_jwt.decode(token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])

        assert decoded == {}

    def test_signed_with_wrong_key_is_not_accepted(self):
        token = create_token({"sub": "user-123"})

        with pytest.raises(jose_jwt.JWTError):
            jose_jwt.decode(token, key="other-key", algorithms=[JWT_ALGORITHM])


class TestDecodeToken:
    def test_round_trip_returns_original_claims(self):
        token = create_token({"sub": "user-123", "type": "access"})

        claims = decode_token(token)

        assert claims["sub"] == "user-123"
        assert claims["type"] == "access"

    def test_returns_dict(self):
        token = create_token({"sub": "user-123"})

        claims = decode_token(token)

        assert isinstance(claims, dict)

    def test_expired_token_raises_unauthorized(self):
        past = datetime.now(tz=UTC) - timedelta(hours=1)
        token = create_token(
            {
                "sub": "user-123",
                "iat": past - timedelta(minutes=5),
                "exp": past,
            }
        )

        with pytest.raises(UnauthorizedError, match="Token expired"):
            decode_token(token)

    def test_malformed_token_raises_unauthorized(self):
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_token("not-a-jwt")

    def test_empty_string_raises_unauthorized(self):
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_token("")

    def test_token_signed_with_other_key_raises_unauthorized(self):
        token = jose_jwt.encode(
            {"sub": "user-123"},
            key="some-other-secret",
            algorithm=JWT_ALGORITHM,
        )

        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_token(token)

    def test_token_signed_with_other_algorithm_raises_unauthorized(self):
        token = jose_jwt.encode(
            {"sub": "user-123"},
            key=JWT_SECRET,
            algorithm="HS512",
        )

        with pytest.raises(UnauthorizedError, match="Invalid token"):
            decode_token(token)

    def test_expired_error_does_not_chain_exception(self):
        """`Token expired.` é levantado com `from None` (sem causa encadeada)."""
        past = datetime.now(tz=UTC) - timedelta(hours=1)
        token = create_token({"sub": "x", "exp": past})

        with pytest.raises(UnauthorizedError) as exc_info:
            decode_token(token)

        assert exc_info.value.__cause__ is None

    def test_invalid_error_chains_original_exception(self):
        """`Invalid token.` preserva a exceção original como causa."""
        with pytest.raises(UnauthorizedError) as exc_info:
            decode_token("garbage")

        assert exc_info.value.__cause__ is not None

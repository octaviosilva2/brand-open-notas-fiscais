from app.core.security.passwords import hash_password, verify_password


class TestHashPassword:
    def test_returns_string(self):
        assert isinstance(hash_password("s3cr3t"), str)

    def test_hash_differs_from_plaintext(self):
        password = "s3cr3t"

        assert hash_password(password) != password

    def test_uses_bcrypt_identifier(self):
        assert hash_password("s3cr3t").startswith("$2b$")

    def test_same_password_produces_different_hashes(self):
        """bcrypt usa salt aleatório, então hashes não devem se repetir."""
        password = "s3cr3t"

        assert hash_password(password) != hash_password(password)


class TestVerifyPassword:
    def test_true_for_correct_password(self):
        password = "s3cr3t"

        assert verify_password(password, hash_password(password)) is True

    def test_false_for_wrong_password(self):
        password_hash = hash_password("s3cr3t")

        assert verify_password("wrong", password_hash) is False

    def test_is_case_sensitive(self):
        password_hash = hash_password("Secret")

        assert verify_password("secret", password_hash) is False

    def test_handles_unicode_passwords(self):
        password = "sénhâ-ação-🔒"

        assert verify_password(password, hash_password(password)) is True


class TestPasswordTruncation:
    def test_bytes_beyond_72_are_ignored(self):
        """A senha é truncada em 72 bytes (limite do bcrypt) antes do hash."""
        base = "a" * 72
        password_hash = hash_password(base)

        assert verify_password(base + "extra-ignored", password_hash) is True

    def test_difference_within_72_bytes_is_significant(self):
        password_hash = hash_password("a" * 72)

        assert verify_password("b" + "a" * 71, password_hash) is False

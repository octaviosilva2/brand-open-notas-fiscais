import pytest

from app.core.validators import (
    validate_cnpj,
    validate_cnpj_or_cpf,
    validate_cpf,
    validate_timezone,
)

VALID_CNPJ = "11.222.333/0001-81"
VALID_CNPJ_DIGITS = "11222333000181"

VALID_CPF = "529.982.247-25"
VALID_CPF_DIGITS = "52998224725"


class TestValidateCnpj:
    def test_accepts_valid_cnpj(self):
        assert validate_cnpj(VALID_CNPJ) == VALID_CNPJ_DIGITS

    def test_returns_only_digits(self):
        assert validate_cnpj(VALID_CNPJ_DIGITS) == VALID_CNPJ_DIGITS

    def test_rejects_fewer_than_14_digits(self):
        with pytest.raises(ValueError, match="14 dígitos"):
            validate_cnpj("1234567890123")

    def test_rejects_more_than_14_digits(self):
        with pytest.raises(ValueError, match="14 dígitos"):
            validate_cnpj("123456789012345")

    def test_rejects_all_same_digits(self):
        with pytest.raises(ValueError, match="CNPJ inválido"):
            validate_cnpj("00000000000000")

    def test_rejects_invalid_first_check_digit(self):
        tampered = VALID_CNPJ_DIGITS[:12] + "0" + VALID_CNPJ_DIGITS[13]
        with pytest.raises(ValueError, match="CNPJ inválido"):
            validate_cnpj(tampered)

    def test_rejects_invalid_second_check_digit(self):
        tampered = VALID_CNPJ_DIGITS[:13] + "0"
        with pytest.raises(ValueError, match="CNPJ inválido"):
            validate_cnpj(tampered)

    def test_result_is_only_digits(self):
        result = validate_cnpj(VALID_CNPJ)
        assert result.isdigit()


class TestValidateCpf:
    def test_accepts_valid_cpf(self):
        assert validate_cpf(VALID_CPF) == VALID_CPF_DIGITS

    def test_returns_only_digits(self):
        assert validate_cpf(VALID_CPF_DIGITS) == VALID_CPF_DIGITS

    def test_rejects_fewer_than_11_digits(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            validate_cpf("1234567890")

    def test_rejects_more_than_11_digits(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            validate_cpf("123456789012")

    def test_rejects_all_same_digits(self):
        with pytest.raises(ValueError, match="CPF inválido"):
            validate_cpf("00000000000")

    def test_rejects_invalid_first_check_digit(self):
        tampered = VALID_CPF_DIGITS[:9] + "0" + VALID_CPF_DIGITS[10]
        with pytest.raises(ValueError, match="CPF inválido"):
            validate_cpf(tampered)

    def test_rejects_invalid_second_check_digit(self):
        tampered = VALID_CPF_DIGITS[:10] + "0"
        with pytest.raises(ValueError, match="CPF inválido"):
            validate_cpf(tampered)

    def test_result_is_only_digits(self):
        result = validate_cpf(VALID_CPF)
        assert result.isdigit()


class TestValidateCnpjOrCpf:
    def test_accepts_valid_cnpj(self):
        assert validate_cnpj_or_cpf(VALID_CNPJ) == VALID_CNPJ_DIGITS

    def test_accepts_valid_cpf(self):
        assert validate_cnpj_or_cpf(VALID_CPF) == VALID_CPF_DIGITS

    def test_rejects_wrong_digit_count(self):
        with pytest.raises(ValueError, match="CNPJ ou CPF"):
            validate_cnpj_or_cpf("12345")

    def test_delegates_cnpj_validation_for_14_digits(self):
        with pytest.raises(ValueError, match="CNPJ inválido"):
            validate_cnpj_or_cpf("00000000000000")

    def test_delegates_cpf_validation_for_11_digits(self):
        with pytest.raises(ValueError, match="CPF inválido"):
            validate_cnpj_or_cpf("00000000000")


class TestValidateTimezone:
    def test_accepts_valid_timezone(self):
        assert validate_timezone("America/Sao_Paulo") == "America/Sao_Paulo"

    def test_accepts_utc(self):
        assert validate_timezone("UTC") == "UTC"

    def test_returns_timezone_unchanged(self):
        tz = "Europe/Berlin"
        assert validate_timezone(tz) == tz

    def test_rejects_invalid_timezone(self):
        with pytest.raises(ValueError, match="Timezone inválida"):
            validate_timezone("Invalid/Timezone")

    def test_error_includes_rejected_value(self):
        invalid_tz = "Foo/Bar"
        with pytest.raises(ValueError, match=invalid_tz):
            validate_timezone(invalid_tz)

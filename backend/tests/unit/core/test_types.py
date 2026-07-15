import dataclasses

from app.core.types import (
    UNSET,
    BaseCommand,
    BaseCreateCommand,
    BaseUpdateCommand,
    Unset,
    _UnsetType,
    is_unset,
)


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleCommand(BaseCommand):
    name: str
    value: int


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleCreateCommand(BaseCreateCommand):
    name: str


@dataclasses.dataclass(frozen=True, slots=True)
class _SampleUpdateCommand(BaseUpdateCommand):
    name: str | _UnsetType = UNSET
    value: int | _UnsetType = UNSET


class TestUnsetType:
    def test_repr_is_unset(self):
        assert repr(_UnsetType()) == "UNSET"

    def test_bool_is_false(self):
        assert bool(_UnsetType()) is False

    def test_is_falsy_in_conditional(self):
        assert not _UnsetType()

    def test_unset_sentinel_is_instance_of_unset_type(self):
        assert isinstance(UNSET, _UnsetType)

    def test_unset_alias_is_unset_type_class(self):
        assert Unset is _UnsetType

    def test_unset_repr(self):
        assert repr(UNSET) == "UNSET"

    def test_unset_is_falsy(self):
        assert not UNSET


class TestIsUnset:
    def test_returns_true_for_unset_sentinel(self):
        assert is_unset(UNSET) is True

    def test_returns_true_for_any_unset_type_instance(self):
        assert is_unset(_UnsetType()) is True

    def test_returns_false_for_none(self):
        assert is_unset(None) is False

    def test_returns_false_for_zero(self):
        assert is_unset(0) is False

    def test_returns_false_for_empty_string(self):
        assert is_unset("") is False

    def test_returns_false_for_false(self):
        assert is_unset(False) is False

    def test_returns_false_for_regular_value(self):
        assert is_unset("value") is False

    def test_returns_false_for_empty_dict(self):
        assert is_unset({}) is False


class TestBaseCommand:
    def test_to_dict_returns_dict(self):
        cmd = _SampleCommand(name="test", value=42)

        result = cmd.to_dict()

        assert isinstance(result, dict)

    def test_to_dict_contains_all_fields(self):
        cmd = _SampleCommand(name="test", value=42)

        result = cmd.to_dict()

        assert result == {"name": "test", "value": 42}

    def test_is_frozen(self):
        cmd = _SampleCommand(name="test", value=1)

        try:
            cmd.name = "other"  # type: ignore[misc]
            raise AssertionError("Deveria ter levantado exceção")
        except dataclasses.FrozenInstanceError, AttributeError:
            pass

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(BaseCommand)


class TestBaseCreateCommand:
    def test_is_base_command_subclass(self):
        assert issubclass(BaseCreateCommand, BaseCommand)

    def test_is_dataclass(self):
        assert dataclasses.is_dataclass(BaseCreateCommand)

    def test_to_dict_inherited(self):
        cmd = _SampleCreateCommand(name="produto")

        assert cmd.to_dict() == {"name": "produto"}

    def test_is_frozen(self):
        cmd = _SampleCreateCommand(name="test")

        try:
            cmd.name = "other"  # type: ignore[misc]
            raise AssertionError("Deveria ter levantado exceção")
        except dataclasses.FrozenInstanceError, AttributeError:
            pass


class TestBaseUpdateCommand:
    def test_is_base_command_subclass(self):
        assert issubclass(BaseUpdateCommand, BaseCommand)

    def test_defined_values_excludes_unset_fields(self):
        cmd = _SampleUpdateCommand(name="novo nome")

        result = cmd.defined_values()

        assert result == {"name": "novo nome"}
        assert "value" not in result

    def test_defined_values_returns_all_when_none_are_unset(self):
        cmd = _SampleUpdateCommand(name="nome", value=10)

        result = cmd.defined_values()

        assert result == {"name": "nome", "value": 10}

    def test_defined_values_returns_empty_when_all_unset(self):
        cmd = _SampleUpdateCommand()

        result = cmd.defined_values()

        assert result == {}

    def test_has_changes_true_when_at_least_one_defined(self):
        cmd = _SampleUpdateCommand(name="nome")

        assert cmd.has_changes() is True

    def test_has_changes_false_when_all_unset(self):
        cmd = _SampleUpdateCommand()

        assert cmd.has_changes() is False

    def test_has_changes_true_when_all_defined(self):
        cmd = _SampleUpdateCommand(name="nome", value=5)

        assert cmd.has_changes() is True

    def test_is_frozen(self):
        cmd = _SampleUpdateCommand(name="test")

        try:
            cmd.name = "other"  # type: ignore[misc]
            raise AssertionError("Deveria ter levantado exceção")
        except dataclasses.FrozenInstanceError, AttributeError:
            pass


class TestDataclassInstance:
    def test_dataclass_satisfies_protocol(self):
        @dataclasses.dataclass
        class Sample:
            x: int

        assert hasattr(Sample, "__dataclass_fields__")

    def test_plain_class_does_not_satisfy_protocol(self):
        class NotADataclass:
            pass

        assert not hasattr(NotADataclass, "__dataclass_fields__")

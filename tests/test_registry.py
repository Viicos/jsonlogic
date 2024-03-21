import pytest

from jsonlogic.core import Operator
from jsonlogic.registry import AlreadyRegistered, OperatorRegistry, UnkownOperator


def test_operator_registry():
    class Var(Operator):
        pass

    registry = OperatorRegistry()
    registry.register("var", Var)

    @registry.register("==")
    class Equal(Operator):
        pass

    assert registry._registry == {
        "var": Var,
        "==": Equal,
    }

    assert registry.get("var") is Var


def test_already_registered():
    class Var(Operator):
        pass

    class Var2(Operator):
        pass

    registry = OperatorRegistry()
    registry.register("var", Var)

    with pytest.raises(AlreadyRegistered) as exc:
        registry.register("var", Var2)

    assert exc.value.operator_id == "var"


def test_force():
    class Var(Operator):
        pass

    class Var2(Operator):
        pass

    registry = OperatorRegistry()
    registry.register("var", Var)
    registry.register("var", Var2, force=True)

    assert registry.get("var") is Var2


def test_get_unknown():
    registry = OperatorRegistry()

    with pytest.raises(UnkownOperator) as exc:
        registry.get("unknown")

    assert exc.value.operator_id == "unknown"


def test_remove():
    class Var(Operator):
        pass

    registry = OperatorRegistry()
    registry.register("var", Var)

    registry.remove("var")

    assert registry._registry == {}

    # Currently doesn't raise
    registry.remove("unknown")


def test_copy():
    class Var(Operator):
        pass

    registry = OperatorRegistry()
    registry.register("var", Var)

    copy = registry.copy()

    assert copy._registry == registry._registry


def test_with_operator():
    class Var(Operator):
        pass

    registry = OperatorRegistry()

    copy = registry.with_operator("var", Var)

    assert copy._registry == {"var": Var}

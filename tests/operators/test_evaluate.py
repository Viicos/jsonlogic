from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, cast

import pytest

from jsonlogic._compat import Self
from jsonlogic.core import JSONLogicExpression, Operator
from jsonlogic.evaluation import EvaluationContext, evaluate
from jsonlogic.operators import operator_registry as base_operator_registry
from jsonlogic.resolving import Unresolvable
from jsonlogic.typing import OperatorArgument


@dataclass
class ReturnsOp(Operator):
    """A test operator returning the provided value during evaluation."""

    return_value: Any

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        assert len(arguments) == 1
        return cls(
            operator=operator,
            return_value=arguments[0],
        )

    def evaluate(self, context: EvaluationContext) -> Any:
        return self.return_value


operator_registry = base_operator_registry.copy(extend={"returns": ReturnsOp})


def as_op(json_logic: dict[str, Any]) -> Operator:
    expr = JSONLogicExpression.from_json(json_logic)
    return cast(Operator, expr.as_operator_tree(operator_registry))


def test_var_dynamic_variable_path() -> None:
    op = as_op({"var": {"returns": "/some_var"}})
    rv = evaluate(
        op,
        data={"some_var": 1},
        data_schema=None,
    )
    assert rv == 1


def test_var_unresolvable_no_default() -> None:
    op = as_op({"var": "/some_var"})

    with pytest.raises(Unresolvable) as exc:
        evaluate(op, data={}, data_schema=None)

    assert exc.value.parsed_reference.reference == "/some_var"


def test_var_unresolvable_default() -> None:
    op = as_op({"var": ["/some_var", 1]})
    rv = evaluate(
        op,
        data={},
        data_schema=None,
    )

    assert rv == 1


def test_var_resolvable_default() -> None:
    op = as_op({"var": ["/some_var", 1]})
    rv = evaluate(
        op,
        data={"some_var": "a"},
        data_schema=None,
    )

    assert rv == "a"


def test_equal_op() -> None:
    op_1 = as_op({"==": [1, "test"]})
    rv = evaluate(
        op_1,
        data={},
        data_schema=None,
    )

    assert rv is False


def test_not_equal_op() -> None:
    op_1 = as_op({"!=": [1, "test"]})
    rv = evaluate(
        op_1,
        data={},
        data_schema=None,
    )

    assert rv is True


def test_if() -> None:
    op = as_op({"if": [False, "string_val", 1, 2.0, "other_string"]})
    rv = evaluate(
        op,
        data={},
        data_schema=None,
    )

    assert rv == 2.0


def test_if_uses_leading_else() -> None:
    op = as_op({"if": [False, "string_val", 0, 2.0, "other_string"]})
    rv = evaluate(
        op,
        data={},
        data_schema=None,
    )

    assert rv == "other_string"


def test_binary_op() -> None:
    # Note: this test is relevant for all the binary operator classes.
    op = as_op({">": [2, 1]})
    rv = evaluate(
        op,
        data={},
        data_schema=None,
    )

    assert rv is True


def test_plus() -> None:
    op_two_operands = as_op({"+": [1, 2]})
    rv = evaluate(
        op_two_operands,
        data={},
        data_schema=None,
    )

    assert rv == 3

    op_three_operands = as_op({"+": [1, 2, 3]})
    rv = evaluate(
        op_three_operands,
        data={},
        data_schema=None,
    )

    assert rv == 6


def test_minus() -> None:
    op_unary = as_op({"-": 1})
    rv = evaluate(
        op_unary,
        data={},
        data_schema=None,
    )

    assert rv == -1

    op_binary = as_op({"-": [2, 1]})
    rv = evaluate(
        op_binary,
        data={},
        data_schema=None,
    )

    assert rv == 1


def test_map() -> None:
    op = as_op({"map": [[1, 2], {"+": [{"var": ""}, 2.0]}]})
    rv = evaluate(op, {}, None)

    assert rv == [3.0, 4.0]


def test_map_op_in_values() -> None:
    op = as_op({"map": [["2000-01-01", {"var": "/my_date"}], {">": [{"var": ""}, "1970-01-01"]}]})

    rv = evaluate(
        op,
        data={"my_date": "1960-01-01"},
        data_schema={"type": "object", "properties": {"my_date": {"type": "string", "format": "date"}}},
        settings={"literal_casts": [date.fromisoformat]},
    )

    assert rv == [True, False]


def test_nested_map() -> None:
    op = as_op(
        {
            "map": [
                [[1, 2], [3, {"var": "/my_number"}]],
                {"var": ""},
            ],
        }
    )

    rv = evaluate(
        op, data={"my_number": 4}, data_schema={"type": "object", "properties": {"my_number": {"type": "integer"}}}
    )

    assert rv == [[1, 2], [3, 4]]


def test_map_root_reference() -> None:
    # The `/@1` reference should resolve to the "" attribute of the top level schema,
    # meaning the variables of the `map` operators are meaningless.
    op = as_op({"map": [["some", "strings"], {"+": [{"var": "/@1"}, 2.0]}]})
    rv = evaluate(op, data={"": 1}, data_schema={"type": "object", "properties": {"": {"type": "integer"}}})
    assert rv == [3.0, 3.0]

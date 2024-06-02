from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from jsonlogic._compat import Self
from jsonlogic.core import JSONLogicExpression, Operator
from jsonlogic.evaluation import EvaluationContext
from jsonlogic.json_schema.types import (
    AnyType,
    ArrayType,
    BooleanType,
    DateType,
    IntegerType,
    JSONSchemaType,
    NumberType,
    StringType,
    UnionType,
)
from jsonlogic.operators import operator_registry as base_operator_registry
from jsonlogic.typechecking import TypecheckContext, typecheck
from jsonlogic.typing import OperatorArgument


@dataclass
class ReturnsOp(Operator):
    """A test operator returning the provided type during typechecking."""

    return_type: JSONSchemaType

    @classmethod
    def from_expression(cls, operator: str, arguments: list[OperatorArgument]) -> Self:
        assert len(arguments) == 1
        return cls(
            operator=operator,
            return_type=arguments[0],  # type: ignore
        )

    def typecheck(self, context: TypecheckContext) -> JSONSchemaType:
        return self.return_type

    def evaluate(self, context: EvaluationContext) -> None:
        return None


operator_registry = base_operator_registry.copy(extend={"returns": ReturnsOp})


def as_op(json_logic: dict[str, Any]) -> Operator:
    expr = JSONLogicExpression.from_json(json_logic)
    return cast(Operator, expr.as_operator_tree(operator_registry))


def test_var_dynamic_variable_path() -> None:
    op_no_diag = as_op({"var": {"returns": StringType()}})
    rt, diagnostics = typecheck(op_no_diag, {})

    assert rt == AnyType()
    assert diagnostics == []

    op_diag = as_op({"var": {"returns": BooleanType()}})
    rt, diagnostics = typecheck(op_diag, {})

    assert rt == AnyType()
    diag = diagnostics[0]
    assert diag.category == "argument_type"
    assert diag.message == "The first argument must be of type string, got boolean"


def test_var_unresolvable_no_default() -> None:
    op = as_op({"var": "/some_var"})
    rt, diagnostics = typecheck(op, {})

    assert rt == AnyType()
    diag = diagnostics[0]

    assert diag.category == "unresolvable_variable"
    assert diag.message == "'/some_var' is unresolvable and no fallback value is provided"


def test_var_unresolvable_default() -> None:
    op = as_op({"var": ["/some_var", 1]})
    rt, diagnostics = typecheck(op, {})

    assert rt == IntegerType()
    diag = diagnostics[0]

    assert diag.category == "unresolvable_variable"
    assert diag.message == "'/some_var' is unresolvable"
    assert diag.type == "warning"


def test_var_resolvable_no_default() -> None:
    op = as_op({"var": "/some_var"})
    rt, diagnostics = typecheck(op, {"type": "object", "properties": {"some_var": {"type": "string"}}})

    assert rt == StringType()
    assert diagnostics == []


def test_var_resolvable_default() -> None:
    op = as_op({"var": ["/some_var", 1]})
    rt, diagnostics = typecheck(op, {"type": "object", "properties": {"some_var": {"type": "string"}}})

    assert rt == UnionType(StringType(), IntegerType())
    assert diagnostics == []


def test_equality_op() -> None:
    # Note: this test is relevant for the `Equal` and `NotEqual` operator classes.
    op_1 = as_op({"==": [1, "test"]})
    rt, diagnostics = typecheck(op_1, {})

    assert rt == BooleanType()
    assert diagnostics == []

    op_2 = as_op({"==": [{"var": "a"}, {"var": "b"}]})
    rt, diagnostics = typecheck(op_2, {})

    assert rt == BooleanType()
    # Should contain diagnostics from the var op:
    assert len(diagnostics) == 2


def test_if_bad_condition() -> None:
    # `DateType` does not support boolean evaluation
    returns_date = {"returns": DateType()}
    op = as_op({"if": [returns_date, "some_value", "other_value"]})
    _, diagnostics = typecheck(op, {})
    diag = diagnostics[0]

    assert diag.category == "argument_type"
    assert diag.message == "Condition 1 should support boolean evaluation"

    op = as_op({"if": [returns_date, "some_value", returns_date, "other_value", "another_value"]})
    _, diagnostics = typecheck(op, {})
    diag_1, diag_2 = diagnostics

    assert diag_1.message == "Condition 1 should support boolean evaluation"
    assert diag_2.message == "Condition 2 should support boolean evaluation"


def test_if() -> None:
    op = as_op({"if": [1, "string_val", 2, 2.0, "other_string"]})
    rt, diagnostics = typecheck(op, {})

    assert rt == UnionType(StringType(), NumberType())
    assert diagnostics == []


def test_binary_op() -> None:
    # Note: this test is relevant for all the binary operator classes.
    op = as_op({">": [2, {"returns": NumberType()}]})
    rt, diagnostics = typecheck(op, {})

    assert rt == BooleanType()
    assert diagnostics == []

    op_fail = as_op({">=": [2, {"returns": DateType()}]})
    rt, diagnostics = typecheck(op_fail, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "operator"
    assert diag.message == 'Operator ">=" not supported for types integer and date'


def test_plus() -> None:
    op_two_operands = as_op({"+": ["a", "b"]})
    rt, diagnostics = typecheck(op_two_operands, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "operator"
    assert diag.message == 'Operator "+" not supported for types string and string'

    op_three_operands = as_op({"+": ["a", 1, 2]})
    rt, diagnostics = typecheck(op_three_operands, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "operator"
    assert diag.message == 'Operator "+" not supported for types string (argument 1) and integer (argument 2)'

    op_ok = as_op({"+": [1, 2, 3, 4]})
    rt, diagnostics = typecheck(op_ok, {})

    assert rt == IntegerType()
    assert diagnostics == []


def test_minus() -> None:
    op_unary = as_op({"-": {"returns": DateType()}})
    rt, diagnostics = typecheck(op_unary, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "operator"
    assert diag.message == 'Operator "-" not supported for type date'

    op_binary = as_op({"-": [{"returns": DateType()}, {"returns": IntegerType()}]})
    rt, diagnostics = typecheck(op_binary, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "operator"
    assert diag.message == 'Operator "-" not supported for type date and integer'

    op_ok = as_op({"-": [1, 1]})
    rt, diagnostics = typecheck(op_ok, {})

    assert rt == IntegerType()
    assert diagnostics == []


def test_map() -> None:
    op_bad_vars = as_op({"map": [1, "irrelevant"]})
    rt, diagnostics = typecheck(op_bad_vars, {})
    diag = diagnostics[0]

    assert rt == AnyType()
    assert diag.category == "argument_type"
    assert diag.message == "The first argument must be of type array, got integer"

    op = as_op({"map": [[1, 2], {"+": [{"var": ""}, 2.0]}]})
    rt, diagnostics = typecheck(op, {})

    assert rt == ArrayType(NumberType())
    assert diagnostics == []


def test_map_op_in_values() -> None:
    op = as_op({"map": [["2000-01-01", {"var": "/my_date"}], {">": [{"var": ""}, "1970-01-01"]}]})

    rt, _ = typecheck(
        op,
        data_schema={"type": "object", "properties": {"my_date": {"type": "string", "format": "date"}}},
        settings={"literal_casts": {date.fromisoformat: DateType}},
    )

    assert rt == ArrayType(BooleanType())


def test_nested_map() -> None:
    op = as_op(
        {
            "map": [
                [[1, 2], [3, {"var": "/my_number"}]],
                {"var": ""},
            ],
        }
    )

    rt, _ = typecheck(op, data_schema={"type": "object", "properties": {"my_number": {"type": "integer"}}})

    assert rt == ArrayType(ArrayType(IntegerType()))


def test_map_root_reference() -> None:
    # The `/@1` reference should resolve to the "" attribute of the top level schema,
    # meaning the variables of the `map` operators are meaningless.
    op = as_op({"map": [["some", "strings"], {"+": [{"var": "/@1"}, 2.0]}]})
    rt, diagnostics = typecheck(op, {"type": "object", "properties": {"": {"type": "integer"}}})

    assert rt == ArrayType(NumberType())
    assert diagnostics == []

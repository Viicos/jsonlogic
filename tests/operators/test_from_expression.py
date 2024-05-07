import pytest

from jsonlogic.core import JSONLogicSyntaxError
from jsonlogic.operators import (
    Equal,
    GreaterThan,
    If,
    Map,
    Minus,
    Plus,
    Var,
)
from jsonlogic.utils import UNSET


def test_var() -> None:
    var_no_default_1 = Var.from_expression("var", ["some.path"])
    assert var_no_default_1.variable_path == "some.path"

    _equal = Equal.from_expression("==", [1, 1])
    var_no_default_2 = Var.from_expression("var", [_equal])
    assert var_no_default_2.variable_path is _equal

    var_default = Var.from_expression("var", ["some.path", 1])
    assert var_default.default_value == 1

    with pytest.raises(JSONLogicSyntaxError, match="'var' expects one or two arguments, got 3"):
        Var.from_expression("var", [1, 2, 3])

    with pytest.raises(JSONLogicSyntaxError, match="Variable path must be a string on an operator, got <class 'list'>"):
        Var.from_expression("var", [["invalid_array"]])


def test_equality_op() -> None:
    # Note: this test is relevant for the `Equal` and `NotEqual` operator classes.
    equal = Equal.from_expression("==", [1, 2])
    assert equal.left == 1
    assert equal.right == 2

    with pytest.raises(JSONLogicSyntaxError, match="'==' expects two arguments, got 3"):
        Equal.from_expression("==", [1, 2, 3])


def test_if() -> None:
    if_ = If.from_expression("if", [1, 2, 3, 4, 5])
    assert if_.if_elses == [(1, 2), (3, 4)]
    assert if_.leading_else == 5

    with pytest.raises(JSONLogicSyntaxError, match="'if' expects at least 3 arguments, got 1"):
        If.from_expression("if", [1])

    with pytest.raises(JSONLogicSyntaxError, match="'if' expects an odd number of arguments, got 6"):
        If.from_expression("if", [1, 2, 3, 4, 5, 6])


def test_binary_op() -> None:
    # Note: this test is relevant for all the binary operator classes.
    greater_than = GreaterThan.from_expression(">", [1, 2])
    assert greater_than.left == 1
    assert greater_than.right == 2

    with pytest.raises(JSONLogicSyntaxError, match="'>' expects two arguments, got 3"):
        GreaterThan.from_expression(">", [1, 2, 3])


def test_plus() -> None:
    plus = Plus.from_expression("+", [1, 2, 3, 4])
    assert plus.arguments == [1, 2, 3, 4]

    with pytest.raises(JSONLogicSyntaxError, match=r"'\+' expects at least two arguments, got 1"):
        Plus.from_expression("+", [1])


def test_minus() -> None:
    minus_unary = Minus.from_expression("-", [1])
    assert minus_unary.left == 1
    assert minus_unary.right is UNSET

    minus = Minus.from_expression("-", [1, 2])
    assert minus.left == 1
    assert minus.right == 2

    with pytest.raises(JSONLogicSyntaxError, match="'-' expects one or two arguments, got 3"):
        Minus.from_expression("-", [1, 2, 3])


def test_map() -> None:
    map = Map.from_expression("map", [[1, 2], 3])
    assert map.vars == [1, 2]
    assert map.func == 3

    with pytest.raises(JSONLogicSyntaxError, match="'map' expects two arguments, got 3"):
        Map.from_expression("map", [1, 2, 3])

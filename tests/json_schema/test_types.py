from __future__ import annotations

from typing import get_args

import pytest

from jsonlogic.json_schema.types import (
    AnyType,
    ArrayType,
    BinaryOp,
    BooleanType,
    DatetimeType,
    DateType,
    DurationType,
    IntegerType,
    JSONSchemaPrimitiveType,
    JSONSchemaType,
    NullType,
    NumberType,
    StringType,
    TupleType,
    UnaryOp,
    UnionType,
    UnsupportedOperation,
    unpack_union,
)

BINARY_OPS: tuple[BinaryOp, ...] = get_args(BinaryOp)
UNARY_OPS: tuple[UnaryOp, ...] = get_args(UnaryOp)


def test_any_type() -> None:
    any_type = AnyType()

    assert any_type.name == "any"

    for unary_op in UNARY_OPS:
        assert any_type.unary_op(unary_op) == AnyType()

    for binary_op in BINARY_OPS:
        assert any_type.binary_op(AnyType(), binary_op) == AnyType()


def test_boolean_type() -> None:
    boolean_type = BooleanType()

    assert boolean_type.name == "boolean"

    assert boolean_type.unary_op("bool") == BooleanType()

    with pytest.raises(UnsupportedOperation):
        boolean_type.unary_op("-")

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, boolean_type.binary_op, AnyType(), binary_op)


def test_number_type() -> None:
    number_type = NumberType()

    assert number_type.name == "number"

    assert number_type.unary_op("-") == NumberType()
    assert number_type.unary_op("bool") == BooleanType()

    for other in [NumberType(), IntegerType()]:
        for op in (">", ">=", "<", "<="):
            assert number_type.binary_op(other, op) == BooleanType()  # type: ignore
        for op in ("+", "-", "*", "/", "%"):
            assert number_type.binary_op(other, op) == NumberType()  # type: ignore

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, number_type.binary_op, AnyType(), binary_op)


def test_integer_type() -> None:
    integer_type = IntegerType()

    assert integer_type.name == "integer"

    assert integer_type.unary_op("-") == IntegerType()
    assert integer_type.unary_op("bool") == BooleanType()

    for other in [NumberType(), IntegerType()]:
        for op in (">", ">=", "<", "<="):
            assert integer_type.binary_op(other, op) == BooleanType()  # type: ignore

        assert integer_type.binary_op(other, "/") == NumberType()

    for op in ("+", "-", "*", "%"):
        assert integer_type.binary_op(NumberType(), op) == NumberType()  # type: ignore
        assert integer_type.binary_op(IntegerType(), op) == IntegerType()  # type: ignore

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, integer_type.binary_op, AnyType(), binary_op)


def test_string_type() -> None:
    string_type = StringType()

    assert string_type.name == "string"

    assert string_type.unary_op("bool") == BooleanType()
    with pytest.raises(UnsupportedOperation):
        string_type.unary_op("-")

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, string_type.binary_op, AnyType(), binary_op)


def test_datetime_type() -> None:
    datetime_type = DatetimeType()

    assert datetime_type.name == "datetime"

    for unary_op in UNARY_OPS:
        pytest.raises(UnsupportedOperation, datetime_type.unary_op, unary_op)

    for op in (">", ">=", "<", "<="):
        assert datetime_type.binary_op(DatetimeType(), op) == BooleanType()

    assert datetime_type.binary_op(DatetimeType(), "-") == DurationType()

    for op in ("+", "-"):
        assert datetime_type.binary_op(DurationType(), op) == DatetimeType()

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, datetime_type.binary_op, AnyType(), binary_op)


def test_date_type() -> None:
    date_type = DateType()

    assert date_type.name == "date"

    for unary_op in UNARY_OPS:
        pytest.raises(UnsupportedOperation, date_type.unary_op, unary_op)

    for op in (">", ">=", "<", "<="):
        assert date_type.binary_op(DateType(), op) == BooleanType()

    assert date_type.binary_op(DateType(), "-") == DurationType()

    for op in ("+", "-"):
        assert date_type.binary_op(DurationType(), op) == DateType()

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, date_type.binary_op, AnyType(), binary_op)


def test_duration_type():
    duration_type = DurationType()

    assert duration_type.name == "duration"

    assert duration_type.unary_op("-") == DurationType()
    with pytest.raises(UnsupportedOperation):
        duration_type.unary_op("bool")

    for op in (">", ">=", "<", "<="):
        assert duration_type.binary_op(DurationType(), op) == BooleanType()

    for op in ("+", "-"):
        assert duration_type.binary_op(DurationType(), op) == DurationType()

    assert duration_type.binary_op(DatetimeType(), "+") == DatetimeType()
    assert duration_type.binary_op(DateType(), "+") == DateType()

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, duration_type.binary_op, AnyType(), binary_op)


def test_null_type():
    null_type = NullType()

    assert null_type.name == "null"

    assert null_type.unary_op("bool") == BooleanType()
    with pytest.raises(UnsupportedOperation):
        null_type.unary_op("-")

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, null_type.binary_op, AnyType(), binary_op)


def test_array_type():
    array_type = ArrayType(NullType())

    assert array_type.name == "array(null)"

    assert array_type.unary_op("bool") == BooleanType()
    with pytest.raises(UnsupportedOperation):
        array_type.unary_op("-")

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, array_type.binary_op, AnyType(), binary_op)


def test_tuple_type():
    tuple_type = TupleType((NullType(), ArrayType(IntegerType())))

    assert tuple_type.name == "tuple(null, array(integer))"

    assert tuple_type.unary_op("bool") == BooleanType()
    with pytest.raises(UnsupportedOperation):
        tuple_type.unary_op("-")

    for binary_op in BINARY_OPS:
        pytest.raises(UnsupportedOperation, tuple_type.binary_op, AnyType(), binary_op)


def test_union_type_constructor():
    assert UnionType(NullType(), NullType(), NullType()) == NullType()
    assert UnionType(NullType(), DatetimeType()).types == {NullType(), DatetimeType()}
    assert UnionType(AnyType(), NullType(), DatetimeType()) == AnyType()


def test_union_type_repr():
    assert repr(UnionType(NullType(), DatetimeType())) == "UnionType(NullType(), DatetimeType())"


def test_union_type():
    union_type = UnionType(DurationType(), IntegerType())

    assert union_type.name == "union(duration, integer)"

    with pytest.raises(UnsupportedOperation):
        union_type.unary_op("bool")
    assert union_type.unary_op("-") == UnionType(DurationType(), IntegerType())

    assert UnionType(NumberType(), IntegerType()).binary_op(NumberType(), "+") == NumberType()
    assert UnionType(NumberType(), IntegerType()).binary_op(IntegerType(), "+") == UnionType(
        NumberType(), IntegerType()
    )


def test_union_type_order_doesnt_matter():
    # A | B == B | A
    assert UnionType(NullType(), BooleanType()) == UnionType(BooleanType(), NullType())


def test_union_types_nested():
    # (A | B) | (C | D) == A | B | C | D
    assert UnionType(UnionType(NullType(), BooleanType()), UnionType(NumberType(), IntegerType())) == UnionType(
        NullType(), BooleanType(), NumberType(), IntegerType()
    )

    # (A | B | C) | (A | B) == A | B | C
    assert UnionType(
        UnionType(NumberType(), IntegerType(), NullType()), UnionType(NumberType(), IntegerType())
    ) == UnionType(NumberType(), IntegerType(), NullType())


def test_types_or_op():
    assert NullType() | BooleanType() == UnionType(NullType(), BooleanType())
    assert NullType() | NullType() == NullType()
    assert UnionType(NullType(), BooleanType()) | UnionType(NumberType(), IntegerType()) == UnionType(
        NullType(), BooleanType(), NumberType(), IntegerType()
    )


def test_unpack_union():
    called_types: list[JSONSchemaType] = []

    class MyType(JSONSchemaPrimitiveType):
        @property
        def name(self) -> str:
            return "mytype"

        @unpack_union
        def binary_op(self, other: JSONSchemaPrimitiveType, op: BinaryOp) -> JSONSchemaType:
            called_types.append(other)
            return other

        def unary_op(self, op: UnaryOp) -> JSONSchemaType:
            return AnyType()

    assert MyType().binary_op(UnionType(BooleanType(), NullType()), "*") == UnionType(BooleanType(), NullType())

    assert called_types == [BooleanType(), NullType()]

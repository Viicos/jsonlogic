from __future__ import annotations

from datetime import date
from typing import Any, Callable, NoReturn

import pytest

from jsonlogic.json_schema import as_json_schema, cast_from_schema, from_json_schema, from_value
from jsonlogic.json_schema.types import (
    AnyType,
    ArrayType,
    BooleanType,
    DateType,
    IntegerType,
    JSONSchemaType,
    NullType,
    NumberType,
    StringType,
    TupleType,
    UnionType,
)
from jsonlogic.typing import JSON, JSONLogicPrimitive


def _raises(value: Any) -> NoReturn:
    raise Exception


class _Unknown:
    pass


@pytest.mark.parametrize(
    ["value", "literal_casts", "expected"],
    [
        (True, {}, BooleanType()),
        (1.0, {}, NumberType()),
        (1, {}, IntegerType()),
        (None, {}, NullType()),
        ("a", {}, StringType()),
        ("2024-01-01", {_raises: AnyType, date.fromisoformat: DateType}, DateType()),
        ("2024-01-01", {}, StringType()),
        ([], {}, ArrayType(AnyType())),
        ([True], {}, ArrayType(BooleanType())),
        ([True, "2024-01-01"], {date.fromisoformat: DateType}, ArrayType(UnionType(BooleanType(), DateType()))),
        pytest.param(_Unknown(), {}, AnyType(), marks=pytest.mark.xfail(reason="No fallback currently impl.")),
    ],
)
def test_from_value(
    value: JSONLogicPrimitive, literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]], expected: JSONSchemaType
) -> None:
    assert from_value(value, literal_casts) == expected


json_schema_params = [
    ({}, {}, AnyType()),
    ({"type": "boolean"}, {}, BooleanType()),
    ({"type": "number"}, {}, NumberType()),
    ({"type": "integer"}, {}, IntegerType()),
    ({"type": "null"}, {}, NullType()),
    ({"type": "string"}, {}, StringType()),
    ({"type": ["boolean", "null"]}, {}, UnionType(BooleanType(), NullType())),
    ({"type": "string", "format": "date"}, {"date": DateType}, DateType()),
    ({"type": ["boolean", "string"], "format": "date"}, {"date": DateType}, UnionType(BooleanType(), DateType())),
    ({"type": "array"}, {}, ArrayType(AnyType())),
    ({"type": "array", "items": {"type": "boolean"}}, {}, ArrayType(BooleanType())),
    (
        {"type": "array", "prefixItems": [{"type": "boolean"}, {"type": "null"}], "minItems": 2, "maxItems": 2},
        {},
        TupleType((BooleanType(), NullType())),
    ),
    (
        {
            "type": "array",
            "prefixItems": [{"type": "array", "items": {"type": "boolean"}}],
            "minItems": 1,
            "maxItems": 1,
        },
        {},
        TupleType((ArrayType(BooleanType()),)),
    ),
]
"""Pytest params to use for both `from_json_schema` and `as_json_schema`.

These are the cases where `from_json_schema(as_json_schema(typ))` acts as the identity function.
"""


@pytest.mark.parametrize(
    ["json_schema", "variable_casts", "expected"],
    [
        *json_schema_params,
        ({"type": ["string"]}, {}, StringType()),
        # Both `minItems` and `maxItems` are required to make it a tuple:
        ({"type": "array", "prefixItems": [{"type": "boolean"}]}, {}, ArrayType(AnyType())),
        ({"type": "array", "prefixItems": [{"type": "boolean"}], "minItems": 1}, {}, ArrayType(AnyType())),
        ({"type": "array", "prefixItems": [{"type": "boolean"}], "maxItems": 1}, {}, ArrayType(AnyType())),
    ],
)
def test_from_json_schema(
    json_schema: dict[str, Any], variable_casts: dict[str, type[JSONSchemaType]], expected: JSONSchemaType
) -> None:
    assert from_json_schema(json_schema, variable_casts) == expected


@pytest.mark.parametrize(
    ["type", "variable_casts", "expected"],
    [(param[2], param[1], param[0]) for param in json_schema_params],  # Arguments order is reversed
)
def test_as_json_schema(
    type: JSONSchemaType, variable_casts: dict[str, type[JSONSchemaType]], expected: dict[str, Any]
) -> None:
    assert as_json_schema(type, variable_casts) == expected

    with pytest.raises(RuntimeError):
        as_json_schema(DateType(), {})


@pytest.mark.parametrize(
    ["value", "json_schema", "variable_casts", "expected"],
    [
        (None, {}, {}, None),
        (True, {}, {}, True),
        (1, {}, {}, 1),
        ("test", {"type": "string"}, {}, "test"),
        ("test", {"type": "string", "format": "testfmt"}, {}, "test"),
        ("test", {"type": "string", "format": "testfmt"}, {"testfmt": lambda s: s + "test"}, "testtest"),
        (["test"], {"type": "array", "items": {"type": "string"}}, {}, ["test"]),
        (["test"], {"type": "array", "items": {"type": "string", "format": "testfmt"}}, {}, ["test"]),
        (
            ["test"],
            {"type": "array", "items": {"type": "string", "format": "testfmt"}},
            {"testfmt": lambda s: s + "test"},
            ["testtest"],
        ),
        (
            ["t", "t"],
            {
                "type": "array",
                "prefixItems": [{"type": "string", "format": "fmt1"}, {"type": "string", "format": "fmt2"}],
            },
            {"fmt1": lambda s: f"{s}1", "fmt2": lambda s: f"{s}2"},
            ["t1", "t2"],
        ),
    ],
)
def test_cast_from_schema(
    value: JSON, json_schema: dict[str, Any], variable_casts: dict[str, Callable[[str], Any]], expected: Any
) -> None:
    assert cast_from_schema(value, json_schema, variable_casts) == expected

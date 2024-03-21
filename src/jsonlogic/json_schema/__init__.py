from __future__ import annotations

from typing import Any, Callable, cast

from jsonlogic._compat import NoneType
from jsonlogic.typing import JSONLogicPrimitive

from .types import (
    AnyType,
    BooleanType,
    IntegerType,
    JSONSchemaType,
    NullType,
    NumberType,
    StringType,
)

_VALUE_TYPE_MAP: dict[type[Any], type[JSONSchemaType]] = {
    bool: BooleanType,
    float: NumberType,
    int: IntegerType,
    NoneType: NullType,
}


def from_value(
    value: JSONLogicPrimitive, literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]]
) -> JSONSchemaType:
    if type(value) in _VALUE_TYPE_MAP:
        return _VALUE_TYPE_MAP[type(value)]()

    if isinstance(value, str):
        for func, js_type in literal_casts.items():
            try:
                func(value)
            except Exception:
                pass
            else:
                return js_type()

        return StringType()

    return AnyType()


_TYPE_MAP: dict[str, type[JSONSchemaType]] = {
    "boolean": BooleanType,
    "number": NumberType,
    "integer": IntegerType,
    "null": NullType,
}


def from_json_schema(json_schema: dict[str, Any], variable_casts: dict[str, type[JSONSchemaType]]) -> JSONSchemaType:
    # TODO support for unions
    js_type = cast(str | None, json_schema.get("type"))
    if js_type in _TYPE_MAP:
        return _TYPE_MAP[js_type]()

    if js_type == "string":
        format = cast(str | None, json_schema.get("format"))

        if format in variable_casts:
            return variable_casts[format]()

        return StringType()

    return AnyType()

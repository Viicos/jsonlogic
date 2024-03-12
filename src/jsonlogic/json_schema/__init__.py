from datetime import date, datetime
from types import NoneType
from typing import Any, Callable, cast

from jsonlogic.typing import JSONLogicPrimitive

from .types import (
    AnyType,
    BooleanType,
    DatetimeType,
    DateType,
    IntegerType,
    JSONSchemaType,
    NullType,
    NumberType,
    StringType,
)

_VALUE_TYPE_MAP: dict[type[Any], JSONSchemaType] = {
    bool: BooleanType(),
    float: NumberType(),
    int: IntegerType(),
    NoneType: NullType(),
}

_VALUE_FORMAT_MAP: dict[Callable[[str], Any], JSONSchemaType] = {
    datetime.fromisoformat: DatetimeType(),
    date.fromisoformat: DateType(),
}


def from_value(value: JSONLogicPrimitive) -> JSONSchemaType:
    if type(value) in _VALUE_TYPE_MAP:
        return _VALUE_TYPE_MAP[type(value)]

    if isinstance(value, str):
        for func, js_type in _VALUE_FORMAT_MAP.items():
            try:
                func(value)
            except Exception:
                pass
            else:
                return js_type

        return StringType()

    return AnyType()


_TYPE_MAP: dict[str, JSONSchemaType] = {
    "boolean": BooleanType(),
    "number": NumberType(),
    "integer": IntegerType(),
    "null": NullType(),
}

_FORMAT_MAP: dict[str, JSONSchemaType] = {
    "date-time": DatetimeType(),
    "date": DateType(),
}


def from_json_schema(json_schema: dict[str, Any]) -> JSONSchemaType:
    # TODO support for unions
    js_type = cast(str | None, json_schema.get("type"))
    if js_type in _TYPE_MAP:
        return _TYPE_MAP[js_type]

    if js_type == "string":
        format = cast(str | None, json_schema.get("format"))

        if format in _FORMAT_MAP:
            return _FORMAT_MAP[format]

        return StringType()

    return AnyType()

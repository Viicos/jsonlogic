from __future__ import annotations

from typing import Any, Callable, cast

from jsonlogic._compat import NoneType
from jsonlogic.typing import JSONLogicPrimitive

from .resolvers import JSONSchemaDotResolver, JSONSchemaPointerResolver, JSONSchemaResolver, Unresolvable
from .types import (
    AnyType,
    ArrayType,
    BooleanType,
    IntegerType,
    JSONSchemaType,
    NullType,
    NumberType,
    StringType,
    TupleType,
    UnionType,
)

__all__ = (
    "JSONSchemaDotResolver",
    "JSONSchemaPointerResolver",
    "JSONSchemaResolver",
    "Unresolvable",
    "from_json_schema",
    "from_value",
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


_PRIMITIVES_TYPE_MAP: dict[str, type[JSONSchemaType]] = {
    "boolean": BooleanType,
    "number": NumberType,
    "integer": IntegerType,
    "null": NullType,
}


def from_json_schema(json_schema: dict[str, Any], variable_casts: dict[str, type[JSONSchemaType]]) -> JSONSchemaType:
    js_types = cast("list[str] | str | None", json_schema.get("type"))
    if js_types is None:
        return AnyType()

    if not isinstance(js_types, list):
        js_types = [js_types]

    def _from_type(js_type: str, json_schema: dict[str, Any]) -> JSONSchemaType:
        if js_type in _PRIMITIVES_TYPE_MAP:
            return _PRIMITIVES_TYPE_MAP[js_type]()

        if js_type == "string":
            format = cast("str | None", json_schema.get("format"))
            if format in variable_casts:
                return variable_casts[format]()

            return StringType()

        if js_type == "array":
            items_type = cast("dict[str, Any] | None", json_schema.get("items"))
            if items_type is None:
                prefix_items = cast("list[dict[str, Any]] | None", json_schema.get("prefixItems"))
                min_items = cast("int | None", json_schema.get("minItems"))
                max_items = cast("int | None", json_schema.get("maxItems"))
                if prefix_items is not None and min_items is not None and min_items == max_items:
                    return TupleType(tuple(from_json_schema(item, variable_casts) for item in prefix_items))

                return ArrayType(AnyType())

            return ArrayType(from_json_schema(items_type, variable_casts))

        return AnyType()

    return UnionType(*(_from_type(js_type, json_schema) for js_type in js_types))

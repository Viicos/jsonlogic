from __future__ import annotations

from typing import Any, Callable, cast

from jsonlogic._compat import NoneType, TypeIs
from jsonlogic.typing import JSON, JSONLogicPrimitive

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
    "as_json_schema",
    "cast_from_schema",
    "from_json_schema",
    "from_value",
)

_VALUE_TYPE_MAP: dict[type[Any], type[JSONSchemaType]] = {
    bool: BooleanType,
    float: NumberType,
    int: IntegerType,
    NoneType: NullType,
}

_PRIMITIVES_TYPE_MAP: dict[str, type[JSONSchemaType]] = {
    "boolean": BooleanType,
    "number": NumberType,
    "integer": IntegerType,
    "null": NullType,
}

_R_PRIMITIVES_TYPE_MAP: dict[type[JSONSchemaType], str] = {
    **{v: k for k, v in _PRIMITIVES_TYPE_MAP.items()},
    StringType: "string",
}


# Defined purely for type checking purposes:
def _is_primitive_not_str(value: object) -> TypeIs[bool | float | None]:
    return type(value) in _VALUE_TYPE_MAP


def from_value(
    value: JSONLogicPrimitive, literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]]
) -> JSONSchemaType:
    if isinstance(value, str):
        for func, js_type in literal_casts.items():
            try:
                func(value)
            except Exception:
                pass
            else:
                return js_type()

        return StringType()

    if _is_primitive_not_str(value):
        return _VALUE_TYPE_MAP[type(value)]()

    # A design decision had to be made: we infer arrays as arrays and not as tuples,
    # even if types are different.
    if value:
        return ArrayType(UnionType(*(from_value(val, literal_casts) for val in value)))

    # Empty array: can't infer type
    return ArrayType(AnyType())


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
            if items_type is not None:
                return ArrayType(from_json_schema(items_type, variable_casts))

            prefix_items = cast("list[dict[str, Any]] | None", json_schema.get("prefixItems"))
            min_items = cast("int | None", json_schema.get("minItems"))
            max_items = cast("int | None", json_schema.get("maxItems"))
            if prefix_items is not None and min_items is not None and min_items == max_items:
                return TupleType(tuple(from_json_schema(item, variable_casts) for item in prefix_items))

            return ArrayType(AnyType())

        return AnyType()

    return UnionType(*(_from_type(js_type, json_schema) for js_type in js_types))


def as_json_schema(type: JSONSchemaType, variable_casts: dict[str, type[JSONSchemaType]]) -> dict[str, Any]:
    type_class = type.__class__
    if type_class in _R_PRIMITIVES_TYPE_MAP:
        return {"type": _R_PRIMITIVES_TYPE_MAP[type_class]}

    if isinstance(type, AnyType):
        return {}

    if isinstance(type, UnionType):
        sub_schemas = [as_json_schema(subtype, variable_casts) for subtype in type.types]
        types = [
            sub_schema.pop("type")  # UnionTypes can't have any, so `"type"` is guaranteed to be present
            for sub_schema in sub_schemas
        ]
        schema = {
            "type": types[0] if len(types) == 1 else types,
        }
        for sub_schema in sub_schemas:
            schema.update(sub_schema)
        return schema

    if isinstance(type, ArrayType):
        items_type = as_json_schema(type.elements_type, variable_casts)
        if items_type:
            return {"type": "array", "items": items_type}
        return {"type": "array"}

    if isinstance(type, TupleType):
        return {
            "type": "array",
            "minItems": len(type.tuple_types),
            "maxItems": len(type.tuple_types),
            "prefixItems": [as_json_schema(subtype, variable_casts) for subtype in type.tuple_types],
        }

    r_variable_casts = {v: k for k, v in variable_casts.items()}

    if type_class in r_variable_casts:
        return {"type": "string", "format": r_variable_casts[type_class]}

    raise RuntimeError(f"Unable to determine JSON Schema for type {type}")


def cast_from_schema(value: JSON, json_schema: dict[str, Any], variable_casts: dict[str, Callable[[str], Any]]) -> Any:
    js_types = cast("list[str] | str | None", json_schema.get("type"))
    if js_types is None:
        return value

    if not isinstance(js_types, list):
        js_types = [js_types]

    if (
        isinstance(value, str)
        and "string" in js_types
        and (cast_func := variable_casts.get(json_schema.get("format")))  # type: ignore
    ):  # fmt: skip
        return cast_func(value)

    if isinstance(value, list) and "array" in js_types:
        items_type = cast("dict[str, Any] | None", json_schema.get("items"))
        if items_type is not None:
            return [cast_from_schema(val, items_type, variable_casts) for val in value]

        prefix_items = cast("list[dict[str, Any]] | None", json_schema.get("prefixItems"))
        if prefix_items is not None:  # TODO check for min/maxItems?
            # TODO return a tuple instead? Needs decision
            return [cast_from_schema(val, item_type, variable_casts) for val, item_type in zip(value, prefix_items)]

    return value

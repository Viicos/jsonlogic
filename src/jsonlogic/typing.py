from typing import TYPE_CHECKING

from ._compat import TypeAlias

if TYPE_CHECKING:
    # This is a hack to make pyright think `TypeAlias` comes from `typing`
    from .typing import TypeAlias

JSONPrimitive: TypeAlias = str | int | float | bool | None
JSONObject: TypeAlias = "dict[str, JSON]"
JSONArray: TypeAlias = "list[JSON]"
JSON: TypeAlias = "JSONPrimitive | JSONArray | JSONObject"

JSONLogicPrimitive: TypeAlias = JSONPrimitive | list[JSONPrimitive]

OperatorArgument: TypeAlias = "JSONLogicPrimitive | Operator"
"""A valid operator argument, either a JSON Logic primitive or an operator."""

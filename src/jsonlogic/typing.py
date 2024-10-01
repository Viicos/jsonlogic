"""Module defining reusable type aliases throughout the library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._compat import TypeAlias

if TYPE_CHECKING:
    # This is a hack to make Pylance think `TypeAlias` comes from `typing`
    from typing import TypeAlias

    from jsonlogic.core import Operator

JSONPrimitive: TypeAlias = "str | int | float | bool | None"
"""A JSON Primitive."""

JSONObject: TypeAlias = "dict[str, JSON]"
JSONArray: TypeAlias = "list[JSON]"
JSON: TypeAlias = "JSONPrimitive | JSONArray | JSONObject"

JSONLogicPrimitive: TypeAlias = "JSONPrimitive | list[JSONLogicPrimitive]"
"""A JSON Logic primitive is recursively defined either as a JSON primitive or a list of JSON Logic primitives.

Such primitives are only considered when dealing with operator arguments:

.. code-block:: json

    {
        "op": [
            "a string", // A valid primitive (in this case a JSON primitive)
            ["a list"], // A list of JSON primitives
            [1, [2, 3]]
        ]
    }
"""

OperatorArgument: TypeAlias = "Operator | JSONLogicPrimitive | list[OperatorArgument]"
"""An operator argument is recursively defined either as a JSON Logic primitive, an operator or a list of
operator arguments.

.. code-block:: json

    {
        "op": [
            {"nested_op": "..."}, // A nested operator
            [1, {"other_op": "..."}],
            ["a list"] // A JSON Logic primitive
        ]
    }
"""

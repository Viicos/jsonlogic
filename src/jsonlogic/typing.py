"""Module defining reusable type aliases throughout the library."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._compat import TypeAlias

if TYPE_CHECKING:
    # This is a hack to make Pylance think `TypeAlias` comes from `typing`
    from typing import TypeAlias

    from jsonlogic.core import Operator

JSONPrimitive: TypeAlias = str | int | float | bool | None
"""A JSON Primitive."""

JSONObject: TypeAlias = "dict[str, JSON]"
JSONArray: TypeAlias = "list[JSON]"
JSON: TypeAlias = "JSONPrimitive | JSONArray | JSONObject"

JSONLogicPrimitive: TypeAlias = JSONPrimitive | list[JSONPrimitive]
"""A JSON Logic primitive is defined as either a JSON primitive or a list of JSON primitives.

Such primitives are only considered when dealing with operator arguments:

.. code-block:: javascript

    {
        "op": [
            "a string", // A valid primitive (in this case a JSON primitive)
            ["a list"] // A list of JSON primitives
        ]
    }
"""

OperatorArgument: TypeAlias = "JSONLogicPrimitive | Operator"
"""A valid operator argument, either a JSON Logic primitive or an operator.

.. code-block:: javascript

    {
        "op": [
            {"nested_op": ...}, // A nested operator
            ["a list"] // A JSON Logic primitive
        ]
    }
"""

from __future__ import annotations

from typing import Any, Callable

from jsonlogic.core import Operator
from jsonlogic.typing import JSON, JSONLogicPrimitive, OperatorArgument

from .evaluation_context import EvaluationContext
from .evaluation_settings import EvaluationSettingsDict


def evaluate(
    operator: Operator, data: JSON, data_schema: dict[str, Any] | None, settings: EvaluationSettingsDict | None = None
) -> Any:
    """Helper function to evaluate an :class:`~jsonlogic.core.Operator`.

    Args:
        operator: The operator to evaluate.
        data: The root data available during evaluation.
        data_schema: The matching JSON Schema describing the root data. This should be the same JSON Schema
            used during typechecking (see :paramref:`~jsonlogic.typechecking.TypecheckContext.root_data_schema`).
        settings: Settings to be used when evaluating an :class:`~jsonlogic.core.Operator`.
            See :class:`EvaluationSettings` for the available settings and default values.
    Returns:
        The evaluated value.
    """
    context = EvaluationContext(data, data_schema, settings)
    return operator.evaluate(context)


# Function analogous to :func:`jsonlogic.json_schema.from_value`
def _cast_value(value: JSONLogicPrimitive, literal_casts: list[Callable[[str], Any]]) -> Any:
    if isinstance(value, str):
        for func in literal_casts:
            try:
                casted_value = func(value)
            except Exception:
                pass
            else:
                return casted_value

    if not isinstance(value, list):
        return value

    return [_cast_value(subval, literal_casts) for subval in value]


def get_value(obj: OperatorArgument, context: EvaluationContext) -> Any:
    """Get the value of an operator argument.

    Args:
        obj: the object to evaluate. If this is an :class:`~jsonlogic.core.Operator`,
            it is evaluated and the value is returned. Otherwise, it must be a
            :data:`~jsonlogic.typing.JSONLogicPrimitive`, and the type is inferred from
            the actual value according to the :attr:`~TypecheckSettings.literal_casts` setting.
        context: The typecheck context.
    """
    if isinstance(obj, Operator):
        return obj.evaluate(context)
    return _cast_value(obj, context.settings.literal_casts)

from __future__ import annotations

from typing import Any

from jsonlogic.core import Operator
from jsonlogic.json_schema import from_value
from jsonlogic.json_schema.types import ArrayType, JSONSchemaType, UnionType
from jsonlogic.typing import OperatorArgument

from .diagnostics import Diagnostic
from .typecheck_context import TypecheckContext
from .typecheck_settings import TypecheckSettingsDict


def typecheck(
    operator: Operator, data_schema: dict[str, Any], settings: TypecheckSettingsDict | None = None
) -> tuple[JSONSchemaType, list[Diagnostic]]:
    """Helper function to typecheck an :class:`~jsonlogic.core.Operator`.

    Args:
        operator: The operator to typecheck.
        data_schema: The JSON Schema of the data that will be provided to the operator during evaluation.
        settings: The typechecking settings to use. See :class:`TypecheckSettings` for
            the available settings and default values.
    Returns:
        A two-tuple, the first element is the JSON Schema type of the operator, the second one
        is a list of generated diagnostics.
    """

    context = TypecheckContext(data_schema, settings)
    root_type = operator.typecheck(context)
    return root_type, context.diagnostics


def get_type(obj: OperatorArgument, context: TypecheckContext) -> JSONSchemaType:
    """Get the JSON Schema type of an operator argument.

    Args:
        obj: the object to typecheck. If this is an :class:`~jsonlogic.core.Operator`,
            it is typechecked and the type is returned. Otherwise, it must be a
            :data:`~jsonlogic.typing.JSONLogicPrimitive`, and the type is inferred from
            the actual value according to the :attr:`~TypecheckSettings.literal_casts` setting.
        context: The typecheck context.
    """
    if isinstance(obj, Operator):
        return obj.typecheck(context)
    if isinstance(obj, list):
        return ArrayType(UnionType(*(get_type(sub_obj, context) for sub_obj in obj)))
    return from_value(obj, context.settings.literal_casts)

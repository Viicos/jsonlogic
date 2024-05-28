from __future__ import annotations

from typing import Any, Literal, overload

from jsonlogic.json_schema import cast_from_schema
from jsonlogic.resolving import resolve_data, resolve_json_schema
from jsonlogic.typing import JSON
from jsonlogic.utils import DataStack

from .evaluation_settings import EvaluationSettings, EvaluationSettingsDict


class EvaluationContext:
    """A context object used when evaluating operators.

    When evaluating an :class:`~jsonlogic.core.Operator`, an instance of this
    class should be used.

    .. code-block:: pycon

        >>> expr = JSONLogicExpression.from_json({"var": "/a_date"})
        >>> root_op = expr.as_operator_tree(operator_registry)
        >>> context = EvaluationContext(
        ...     data={"a_date": "1970-01-01"},
        ...     data_schema={
        ...         "type": "object",
        ...         "properties": {
        ...             "a_date": {"type": "string", "format": "date"},
        ...         },
        ...     },
        ... )
        >>> root_op.evaluate(context)
        datetime.date(1970, 1, 1)

    Args:
        root_data: The root data available during evaluation.
        data_schema: The matching JSON Schema describing the root data. This should be the same JSON Schema
            used during typechecking (see :paramref:`~jsonlogic.typechecking.TypecheckContext.root_data_schema`).
        settings: Settings to be used when evaluating an :class:`~jsonlogic.core.Operator`.
            See :class:`EvaluationSettings` for the available settings and default values.
    """

    def __init__(
        self, root_data: JSON, data_schema: dict[str, Any] | None = None, settings: EvaluationSettingsDict | None = None
    ) -> None:
        self.data_stack = DataStack((root_data, data_schema))
        self.settings = EvaluationSettings.from_dict(settings) if settings is not None else EvaluationSettings()

    @overload
    def resolve_variable(self, reference: str, *, bare: Literal[True]) -> JSON: ...

    @overload
    def resolve_variable(self, reference: str, *, bare: Literal[False] = ...) -> Any: ...

    def resolve_variable(self, reference: str, *, bare: bool = False) -> JSON | Any:
        """Resolve a variable given the string reference pointing to it.

        The format of the reference should match the reference parser defined
        in the :class:`EvaluationSettings`.

        Args:
            reference: The string reference of the variable.
            bare: Whether the resolved value should be casted to a specific Python
                type according to the matching JSON Schema. Note that this will only
                be possible if a :paramref:`~EvaluationContext.data_schema` was provided.
        """
        parsed_reference, scope = self.settings.reference_parser(reference)
        root_data, root_schema = self.data_stack.get(scope)
        bare_value = resolve_data(parsed_reference, root_data)
        if bare or root_schema is None:
            return bare_value

        schema = resolve_json_schema(parsed_reference, root_schema)
        return cast_from_schema(bare_value, schema, self.settings.variable_casts)

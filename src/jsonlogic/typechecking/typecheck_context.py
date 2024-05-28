from __future__ import annotations

from typing import Any

from jsonlogic.core import Operator
from jsonlogic.resolving import resolve_json_schema
from jsonlogic.utils import DataStack

from .diagnostics import Diagnostic, DiagnosticCategory, DiagnosticType
from .typecheck_settings import TypecheckSettings, TypecheckSettingsDict


class TypecheckContext:
    """A context object used when typechecking operators.

    When typechecking an :class:`~jsonlogic.core.Operator`, an instance of this
    class should be used.

    .. code-block:: pycon

        >>> expr = ...
        >>> root_op = expr.as_operator_tree(operator_registry)
        >>> context = TypecheckContext(
        ...     root_data_schema={"type": "object", "properties": ...},
        ...     settings={
        ...         "diagnostics": {"argument_type": "warning"},
        ...     },
        ... )
        >>> root_op.typecheck(context)
        >>> context.diagnostics
        [Diagnostic(message="...", ...)]

    Args:
        root_data_schema: The root JSON Schema describing the available data when the operator
            will be evaluated.
        settings: Settings to be used when typechecking an :class:`~jsonlogic.core.Operator`.
            See :class:`TypecheckSettings` for the available settings and default values.
    """

    def __init__(self, root_data_schema: dict[str, Any], settings: TypecheckSettingsDict | None = None) -> None:
        self.data_stack = DataStack(root_data_schema)
        self.settings = TypecheckSettings.from_dict(settings) if settings is not None else TypecheckSettings()
        self.diagnostics: list[Diagnostic] = []

    @property
    def current_schema(self) -> dict[str, Any]:
        """The data JSON Schema in the current evaluation scope."""
        return self.data_stack.tail

    def resolve_variable(self, reference: str) -> dict[str, Any]:
        parsed_reference, scope = self.settings.reference_parser(reference)
        schema = self.data_stack.get(scope)
        return resolve_json_schema(parsed_reference, schema)

    def add_diagnostic(
        self, message: str, category: DiagnosticCategory, operator: Operator, type: DiagnosticType | None = None
    ) -> None:
        """Add a diagnostic during typechecking.

        Args:
            message: The message of the diagnostic.
            category: The category of the diagnostic.
            operator: The operator that emitted the diagnostic.
            type: The type of the diagnostic. If not provided (the default), the type
                will be deduced from the settings.
        """
        type = type or getattr(self.settings.diagnostics, category)
        if type is not None:
            self.diagnostics.append(Diagnostic(message, category, type, operator))

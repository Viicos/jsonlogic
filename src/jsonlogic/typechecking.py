"""Utilities related to operator type checking."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable, Literal, TypedDict

from ._compat import TypeAlias
from .core import Operator
from .json_schema import JSONSchemaPointerResolver, JSONSchemaResolver, from_value
from .json_schema.types import DatetimeType, DateType, DurationType, JSONSchemaType
from .typing import OperatorArgument
from .utils import DataStack

DiagnosticType: TypeAlias = Literal["error", "warning", "information"]
"""The type of a diagnostic. Currently, a diagnostic can be one of the types:

- ``"error"``
- ``"warning"``
- ``"information"``.

A diagnostic is thus not necessarily an error. In the future, other types might be supported.
"""

DiagnosticCategory: TypeAlias = Literal["general", "argument_type", "operator", "unresolvable_variable"]
"""The category of a diagnostic. For generic diagnostics, ``"general"`` can be used."""


@dataclass
class Diagnostic:
    """A diagnostic emitted during typechecking."""

    message: str
    """The message of the diagnostic."""

    category: DiagnosticCategory
    """The category of the diagnostic."""

    type: DiagnosticType
    """The type of the diagnostic."""

    operator: Operator
    """The operator that emitted the diagnostic."""


class DiagnosticsConfig(TypedDict, total=False):
    general: DiagnosticType | None
    """A general diagnostic.

    Default: :python:`"error"`.
    """

    argument_type: DiagnosticType | None
    """An argument has the wrong type.

    Default: :python:`"error"`.
    """

    operator: DiagnosticType | None
    """Operator not supported for type(s).

    Default: :python:`"error"`.
    """

    unresolvable_variable: DiagnosticType | None
    """Variable in unresolvable.

    Default: :python:`"error"`.
    """


class SettingsDict(TypedDict, total=False):
    """Settings dict used when typechecking an :class:`~jsonlogic.core.Operator`."""

    # fail_fast: bool
    # """Whether to stop typechecking on the first error.

    # Default: ``False``.
    # """

    variable_resolver: type[JSONSchemaResolver]
    """A JSON Schema variable resolver to use when resolving variables.

    Default: :class:`JSONSchemaPointerResolver`.
    """

    variable_casts: dict[str, type[JSONSchemaType]]
    """A mapping between `JSON Schema formats`_ and their corresponding
    :class:`~jsonlogic.json_schema.types.JSONSchemaType`.

    When an operator makes use of the provided data JSON Schema to read variables
    (such as the ``"var"`` operator), such variables with a type of `"string"`
    might have a format provided. To allow for features specific to these formats,
    such strings can be inferred as a specific JSON :class:`~jsonlogic.json_schema.types.JSONSchemaType`.

    Default: :python:`{"date": DateType, "date-time": DatetimeType}`.

    .. _JSON Schema formats: https://json-schema.org/understanding-json-schema/reference/string#built-in-formats
    """

    literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]]
    """A mapping between conversion callables and their corresponding
    :class:`~jsonlogic.json_schema.types.JSONSchemaType`.

    When a literal string value is encountered in a JSON Logic expression,
    it might be beneficial to infer the :class:`~jsonlogic.json_schema.types.JSONSchemaType`
    from the format of the string. The callable must take a single string argument
    and raise any exception if the format is invalid.

    Default: :python:`{datetime.fromisoformat: DatetimeType, date.fromisoformat: DateType}`.

    .. warning::

        The order in which the conversion callables are defined matters. Each
        callable will be applied one after the other until no exception is raised.
    """

    diagnostics: DiagnosticsConfig
    """Configuration of type for diagnostics.

    This is a mapping between the emitted diagnostic categories and the
    corresponding type (e.g. :python:`"error"` or  :python:`"warning"`).
    """


default_settings: SettingsDict = {
    "variable_resolver": JSONSchemaPointerResolver,
    "variable_casts": {
        "date": DateType,
        "date-time": DatetimeType,
        "duration": DurationType,
    },
    "literal_casts": {
        datetime.fromisoformat: DatetimeType,
        date.fromisoformat: DateType,
    },
    "diagnostics": {
        "argument_type": "error",
        "operator": "error",
    },
}


class TypecheckContext:
    """A context object used when typechecking operators.

    When typechecking an :class:`~jsonlogic.core.Operator`, a instance of this
    class should be used.

    .. code-block:: pycon

        >>> expr = ...
        >>> root_op = expr.as_operator_tree(operator_registry)
        >>> context = TypecheckContext(
        >>>     root_data_schema={"type": "object", "properties": ...},
        >>>     settings={
        >>>         "diagnostics": {"argument_type": "warning"},
        >>>     },
        >>> )
        >>> root_op.typecheck(context)
        >>> context.diagnostics
        [Diagnostic(message="...", ...)]

    Args:
        root_data_schema: The root JSON Schema describing the available data when the operator
            will be evaluated.
        settings: Settings to be used when typechecking an :class:`~jsonlogic.core.Operator`.
            See :class:`SettingsDict` for the available settings and default values.
    """

    def __init__(self, root_data_schema: dict[str, Any], settings: SettingsDict | None = None) -> None:
        self.data_stack = DataStack(root_data_schema)
        self.settings = self._merge_settings(settings, default_settings) if settings is not None else default_settings
        self.json_schema_resolver = self.settings["variable_resolver"](self.data_stack)
        self.diagnostics: list[Diagnostic] = []

    def _merge_settings(self, settings: SettingsDict, defaults: SettingsDict) -> SettingsDict:
        defaults = deepcopy(defaults)
        for k, v in defaults.items():
            if k in settings:
                if isinstance(v, dict):
                    defaults[k] = self._merge_settings(settings[k], v)  # type: ignore
                else:
                    defaults[k] = settings[k]

        return defaults

    @property
    def current_schema(self) -> dict[str, Any]:
        """The data JSON Schema in the current evaluation scope."""
        return self.data_stack.tail

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
        type = type or self.settings["diagnostics"][category]
        if type is not None:
            self.diagnostics.append(Diagnostic(message, category, type, operator))


def typecheck(
    operator: Operator, data_schema: dict[str, Any], settings: SettingsDict | None = None
) -> tuple[JSONSchemaType, list[Diagnostic]]:
    """Helper function to typecheck an :class:`~jsonlogic.core.Operator`.

    Args:
        operator: The operator to typecheck.
        data_schema: The JSON Schema of the data that will be provided to the operator during evaluation.
        settings: The typechecking settings to use. See :class:`SettingsDict` See :class:`SettingsDict` for
            the available settings and default values.
    Returns:
        A two-tuple, the first element being the JSON Schema type of the operator, the second one
            being a list of the generated diagnostics.
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
            the actual value according to the :attr:`~SettingsDict.literal_casts` setting.
        context: The typecheck context.
    """
    if isinstance(obj, Operator):
        return obj.typecheck(context)
    return from_value(obj, context.settings["literal_casts"])

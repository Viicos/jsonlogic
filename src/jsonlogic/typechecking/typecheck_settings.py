from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, TypedDict

from jsonlogic._compat import Self
from jsonlogic.json_schema import JSONSchemaResolver
from jsonlogic.json_schema.resolvers import JSONSchemaPointerResolver
from jsonlogic.json_schema.types import DatetimeType, DateType, JSONSchemaType

from .diagnostics import DiagnosticType


def _d_variable_casts() -> dict[str, type[JSONSchemaType]]:
    return {
        "date": DateType,
        "date-time": DatetimeType,
    }


def _d_literal_casts() -> dict[Callable[[str], Any], type[JSONSchemaType]]:
    return {datetime.fromisoformat: DatetimeType, date.fromisoformat: DateType}


@dataclass
class DiagnosticsConfig:
    general: DiagnosticType | None = "error"
    """A general diagnostic.

    Default: :python:`"error"`.
    """

    argument_type: DiagnosticType | None = "error"
    """An argument has the wrong type.

    Default: :python:`"error"`.
    """

    operator: DiagnosticType | None = "error"
    """Operator not supported for type(s).

    Default: :python:`"error"`.
    """

    unresolvable_variable: DiagnosticType | None = "error"
    """Variable in unresolvable.

    Default: :python:`"error"`.
    """


@dataclass
class TypecheckSettings:
    """Settings used when typechecking an :class:`~jsonlogic.core.Operator`."""

    # fail_fast: bool
    # """Whether to stop typechecking on the first error.

    # Default: ``False``.
    # """

    variable_resolver: type[JSONSchemaResolver] = JSONSchemaPointerResolver
    """A JSON Schema variable resolver to use when resolving variables.

    Default: :class:`JSONSchemaPointerResolver`.
    """

    variable_casts: dict[str, type[JSONSchemaType]] = field(default_factory=_d_variable_casts)
    """A mapping between `JSON Schema formats`_ and their corresponding
    :class:`~jsonlogic.json_schema.types.JSONSchemaType`.

    When an operator makes use of the provided data JSON Schema to read variables
    (such as the ``"var"`` operator), such variables with a type of `"string"`
    might have a format provided. To allow for features specific to these formats,
    such strings can be inferred as a specific JSON :class:`~jsonlogic.json_schema.types.JSONSchemaType`.

    Default: :python:`{"date": DateType, "date-time": DatetimeType}`.

    .. _JSON Schema formats: https://json-schema.org/understanding-json-schema/reference/string#built-in-formats
    """

    literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]] = field(default_factory=_d_literal_casts)
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

    diagnostics: DiagnosticsConfig = field(default_factory=DiagnosticsConfig)
    """Configuration of type for diagnostics.

    This is a mapping between the emitted diagnostic categories and the
    corresponding type (e.g. :python:`"error"` or  :python:`"warning"`).

    Default: see :class:`DiagnosticsConfig`.
    """

    @classmethod
    def from_dict(cls, dct: TypecheckSettingsDict, /) -> Self:
        init_dct: dict[str, Any] = {}
        if (variable_resolver := dct.get("variable_resolver")) is not None:
            init_dct["variable_resolver"] = variable_resolver

        variable_casts = dct.get("variable_casts")
        if variable_casts is None:
            variable_casts = {**_d_variable_casts(), **dct.get("extend_variable_casts", {})}
        init_dct["variable_casts"] = variable_casts

        literal_casts = dct.get("literal_casts")
        if literal_casts is None:
            literal_casts = {**_d_literal_casts(), **dct.get("extend_literal_casts", {})}
        init_dct["literal_casts"] = literal_casts

        diagnostics_dct = dct.get("diagnostics", {})
        init_dct["diagnostics"] = DiagnosticsConfig(**diagnostics_dct)

        return cls(**init_dct)


class DiagnosticsConfigDict(TypedDict, total=False):
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


class TypecheckSettingsDict(TypedDict, total=False):
    """Settings used when typechecking an :class:`~jsonlogic.core.Operator`."""

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

    extend_variable_casts: dict[str, type[JSONSchemaType]]
    """A mapping between `JSON Schema formats`_ and their corresponding
    :class:`~jsonlogic.json_schema.types.JSONSchemaType`, extending the default values.
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

    extend_literal_casts: dict[Callable[[str], Any], type[JSONSchemaType]]
    """A mapping between conversion callables and their corresponding
    :class:`~jsonlogic.json_schema.types.JSONSchemaType`, extending the default values.
    """

    diagnostics: DiagnosticsConfigDict
    """Configuration of type for diagnostics.

    This is a mapping between the emitted diagnostic categories and the
    corresponding type (e.g. :python:`"error"` or  :python:`"warning"`).

    Default: see :class:`DiagnosticsConfigDict`.
    """

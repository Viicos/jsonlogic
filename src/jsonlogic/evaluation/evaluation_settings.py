from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, TypedDict

from jsonlogic._compat import Self
from jsonlogic.resolving import PointerReferenceParser, ReferenceParser


def _d_variable_casts() -> dict[str, Callable[[str], Any]]:
    return {
        "date": date.fromisoformat,
        "date-time": datetime.fromisoformat,
    }


@dataclass
class EvaluationSettings:
    """Settings used when evaluating an :class:`~jsonlogic.core.Operator`."""

    reference_parser: ReferenceParser = field(default_factory=PointerReferenceParser)
    """A reference parser instance to use when resolving variables.

    Default: :class:`~jsonlogic.resolving.PointerReferenceParser`.
    """

    variable_casts: dict[str, Callable[[str], Any]] = field(default_factory=_d_variable_casts)
    """A mapping between `JSON Schema formats`_ and their corresponding conversion callable.

    When an operator reads variables from the provided data (such as the ``"var"`` operator),
    such variables of type :class:`str` may be converted to a specific Python type if
    the corresponding JSON Schema of the data was provided during evaluation.

    This setting is analogous to the :attr:`~jsonlogic.typechecking.TypecheckSettings.variable_casts`
    configuration of the :class:`~jsonlogic.typechecking.TypecheckSettings` class.

    Default: :python:`{"date": date.fromisoformat, "date-time": datetime.fromisoformat}`.

    .. _JSON Schema formats: https://json-schema.org/understanding-json-schema/reference/string#built-in-formats
    """

    literal_casts: list[Callable[[str], Any]] = field(default_factory=list)
    """A list of conversion callables to try when encountering a literal string value during evaluation.

    When a literal string value is encountered in a JSON Logic expression, it might be
    beneficial to convert it to a specific Python type.

    This setting is analogous to the :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts`
    configuration of the :class:`~jsonlogic.typechecking.TypecheckSettings` class.

    Default: :python:`[]` (no cast).

    .. warning::

        The order in which the conversion callables are defined matters. Each
        callable will be applied one after the other until no exception is raised.
    """

    @classmethod
    def from_dict(cls, dct: EvaluationSettingsDict, /) -> Self:
        return cls(**dct)


class EvaluationSettingsDict(TypedDict, total=False):
    """Settings used when evaluating an :class:`~jsonlogic.core.Operator`."""

    reference_parser: ReferenceParser
    """A reference parser instance to use when resolving variables.

    Default: :class:`~jsonlogic.resolving.PointerReferenceParser`.
    """

    variable_casts: dict[str, Callable[[str], Any]]
    """A mapping between `JSON Schema formats`_ and their corresponding conversion callable.

    When an operator reads variables from the provided data (such as the ``"var"`` operator),
    such variables of type :class:`str` may be converted to a specific Python type if
    the corresponding JSON Schema of the data was provided during evaluation.

    This setting is analogous to the :attr:`~jsonlogic.typechecking.TypecheckSettings.variable_casts`
    configuration of the :class:`~jsonlogic.typechecking.TypecheckSettings` class.

    Default: :python:`{"date": date.fromisoformat, "date-time": datetime.fromisoformat}`.

    .. _JSON Schema formats: https://json-schema.org/understanding-json-schema/reference/string#built-in-formats
    """

    literal_casts: list[Callable[[str], Any]]
    """A list of conversion callables to try when encountering a literal string value during evaluation.

    When a literal string value is encountered in a JSON Logic expression, it might be
    beneficial to convert it to a specific Python type.

    This setting is analogous to the :attr:`~jsonlogic.typechecking.TypecheckSettings.literal_casts`
    configuration of the :class:`~jsonlogic.typechecking.TypecheckSettings` class.

    Default: :python:`[]` (no cast).

    .. warning::

        The order in which the conversion callables are defined matters. Each
        callable will be applied one after the other until no exception is raised.
    """

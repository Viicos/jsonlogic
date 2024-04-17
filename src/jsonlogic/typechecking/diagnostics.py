from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from jsonlogic._compat import TypeAlias
from jsonlogic.core import Operator

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

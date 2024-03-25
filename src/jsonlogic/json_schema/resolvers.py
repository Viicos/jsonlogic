from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import unquote

from jsonlogic.utils import DataStack

_scope_specifier_re = re.compile(r"@(\d+)")


class Unresolvable(Exception):
    """A reference is unresolvable."""

    # TODO `details` argument, providing more info?
    def __init__(self, reference: str, /) -> None:
        self.reference = reference


class JSONSchemaResolver(ABC):
    """Resolves the (sub) JSON Schema at the given pointer.

    The implementation of the "reference" is managed by subclasses.
    """

    def __init__(self, data_stack: DataStack[dict[str, Any]]) -> None:
        self.data_stack = data_stack

    @abstractmethod
    def parse(self, reference: str) -> tuple[list[str], dict[str, Any]]:
        pass

    def resolve(self, reference: str) -> dict[str, Any]:
        segments, schema = self.parse(reference)

        for segment in segments:
            schema_type = schema.get("type")

            if schema_type == "object":
                try:
                    schema = schema["properties"][segment]
                    continue
                except KeyError as e:
                    raise Unresolvable(reference) from e
            if schema_type == "array":
                try:
                    int(segment)
                    schema = schema["items"]
                    continue
                except (ValueError, KeyError) as e:
                    raise Unresolvable(reference) from e

            raise Unresolvable(reference)

        return schema


class JSONSchemaDotResolver(JSONSchemaResolver):
    """Resolves the (sub) JSON Schema at the given dotted path."""

    def parse(self, reference: str) -> tuple[list[str], dict[str, Any]]:
        scope_search = _scope_specifier_re.search(reference)
        if scope_search is not None:
            scope_ref = int(scope_search.group(1))
            reference = reference.rsplit("@", 1)[0]
        else:
            scope_ref = 0

        try:
            schema = self.data_stack.get(scope_ref)
        except IndexError as e:
            raise Unresolvable(reference) from e

        segments = reference.split(".")

        return (segments, schema)


class JSONSchemaPointerResolver(JSONSchemaResolver):
    """Resolves the (sub) JSON Schema at the given JSON Pointer, according to :rfc:`6901`.

    The :rfc:`6901` specification is extended with to support accessing specific evaluation scopes.
    """

    def parse(self, reference: str) -> tuple[list[str], dict[str, Any]]:
        # Implementation inspired from the `referencing` library

        scope_search = _scope_specifier_re.search(reference)
        if scope_search is not None:
            scope_ref = int(scope_search.group(1))
            reference = reference.rsplit("@", 1)[0]
        else:
            scope_ref = 0

        try:
            schema = self.data_stack.get(scope_ref)
        except IndexError as e:
            raise Unresolvable(reference) from e

        segments = [
            segment.replace("~2", "@").replace("~1", "/").replace("~0", "~")
            for segment in unquote(reference[1:]).split("/")
        ]

        return (segments, schema)

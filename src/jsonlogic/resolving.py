from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import unquote

from .typing import JSON


@dataclass
class ParsedReference:
    reference: str
    """The original string representation of the reference."""

    segments: list[str]
    """The parsed reference, as a list of string bits."""


class Unresolvable(Exception):
    """A reference is unresolvable."""

    def __init__(self, parsed_reference: ParsedReference, /) -> None:
        self.parsed_reference = parsed_reference


_scope_specifier_re = re.compile(r"@(\d+)")


class ReferenceParser(Protocol):
    """A callback protocol used to parse a string reference."""

    def __call__(self, reference: str) -> tuple[ParsedReference, int]: ...


class BaseReferenceParser(ABC, ReferenceParser):
    """An abstract reference parser that supports specifying a scope in the reference.

    A scope specifier is an optional string appended to the end of the reference.
    It consists of an ``@`` sign followed by a positive number (possibly null), indicating
    the index of the data stack to use before resolving the reference against the
    corresponding data. If not provided, a scope value of ``0`` is implied (the current data).

    This scope specifier allows referencing variables higher up in the stack, e.g. when
    using operators such as *map* or *reduce*.

    The actual segment parsing logic is implemented by subclasses.
    """

    def parse_scope(self, reference: str) -> tuple[str, int]:
        scope_search = _scope_specifier_re.search(reference)
        if scope_search is not None:
            scope_ref = int(scope_search.group(1))
            reference = reference.rsplit("@", 1)[0]
        else:
            scope_ref = 0

        return reference, scope_ref

    @abstractmethod
    def __call__(self, reference: str) -> tuple[ParsedReference, int]:
        pass


class DotReferenceParser(BaseReferenceParser):
    """A reference parser able to parse references with a dot-notation.

    This implements the `reference format`_ of the original JsonLogic project.

    .. caution::

        Using the dot-notation reference format can be confusing when dots are present
        in actual data keys. For example, with the reference ``"path.to"`` and
        the following data:

        .. code-block:: json

            {
                "path": {"to": 1},
                "path.to": 2
            }

        The resolved data can be unexpected. For this reason, it is recommended to use the
        :class:`PointerReferenceParser` which provides an escape mechanism.

    .. _`reference format`: https://jsonlogic.com/operations.html#var
    """

    def __call__(self, reference: str) -> tuple[ParsedReference, int]:
        reference, scope = self.parse_scope(reference)

        return ParsedReference(reference, reference.split(".")), scope


class PointerReferenceParser(BaseReferenceParser):
    """A reference parser able to parse JSON Pointer references, as specified by :rfc:`6901`."""

    def __call__(self, reference: str) -> tuple[ParsedReference, int]:
        reference, scope = self.parse_scope(reference)
        segments = [
            segment.replace("~2", "@").replace("~1", "/").replace("~0", "~")
            for segment in unquote(reference[1:]).split("/")
        ]

        return ParsedReference(reference, segments), scope


def resolve_json_schema(parsed_reference: ParsedReference, schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve the (sub) JSON Schema by looking up by the parsed reference.

    Args:
        parsed_reference: The parsed reference to use.
        schema: The schema to be used when resolving the reference.

    Returns:
        The resolved (sub) JSON Schema.

    Example:

        .. code-block:: python

            ref = PointerReferenceParser()("/path/123")
            schema = {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                    },
                },
            }
            assert resolve_json_schema(ref, schema) == {"type": "string"}
    """

    for segment in parsed_reference.segments:
        schema_type = schema.get("type")

        if schema_type == "object":
            try:
                schema = schema["properties"][segment]
                continue
            except KeyError as e:
                raise Unresolvable(parsed_reference) from e
        if schema_type == "array":
            try:
                int(segment)
                schema = schema["items"]
                continue
            except (ValueError, KeyError) as e:
                raise Unresolvable(parsed_reference) from e

        raise Unresolvable(parsed_reference)

    return schema


def resolve_data(parsed_reference: ParsedReference, data: JSON) -> JSON:
    """Resolve the data by looking up by the parsed reference.

    Args:
        parsed_reference: The parsed reference to use.
        data: The data to be used when resolving the reference.

    Returns:
        The resolved data.

    Example:

        .. code-block:: python

            ref = PointerReferenceParser()("/path/0")
            data = {
                "path": ["some_value"]
            }
            assert resolve_data(ref, data) == "some_value"
    """

    for segment in parsed_reference.segments:
        if isinstance(data, dict):
            try:
                data = data[segment]
                continue
            except KeyError as e:
                raise Unresolvable(parsed_reference) from e
        if isinstance(data, list):
            try:
                index = int(segment)
                data = data[index]
                continue
            except (ValueError, KeyError) as e:
                raise Unresolvable(parsed_reference) from e

        raise Unresolvable(parsed_reference)

    return data

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from urllib.parse import unquote

from jsonlogic.utils import DataStack

PointerT = TypeVar("PointerT")


class Unresolvable(Exception, Generic[PointerT]):
    """A pointer is unresolvable."""

    # TODO `details` argument, providing more info?
    def __init__(self, pointer: PointerT, /) -> None:
        self.pointer = pointer


class JSONSchemaResolver(ABC, Generic[PointerT]):
    """Resolves the (sub) JSON Schema at the given pointer.

    The implementation of the "pointer" is managed by subclasses.
    """

    def __init__(self, data_stack: DataStack[dict[str, Any]]) -> None:
        self.data_stack = data_stack

    @abstractmethod
    def resolve(self, pointer: PointerT) -> dict[str, Any]:
        pass


class JSONSchemaPointerResolver(JSONSchemaResolver[str]):
    """Resolves the (sub) JSON Schema at the given JSON Pointer, according to :rfc:`6901`."""

    def resolve(self, pointer: str) -> dict[str, Any]:
        # Implementation inspired from the `referencing` library
        schema = self.data_stack.tail
        for segment in unquote(pointer[1:]).split("/"):
            schema_type = schema.get("type")
            parsed_segment = segment.replace("~1", "/").replace("~0", "~")
            if schema_type == "object":
                try:
                    schema = schema["properties"][parsed_segment]
                    continue
                except KeyError as e:
                    raise Unresolvable(pointer) from e
            if schema_type == "array":
                try:
                    int(parsed_segment)
                except ValueError as e:
                    raise Unresolvable(pointer) from e
                schema = schema["items"]
        return schema

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from urllib.parse import unquote

PointerT = TypeVar("PointerT")


class Unresolvable(Exception, Generic[PointerT]):
    """A pointer was unresolvable."""

    # TODO `details` argument, providing more info?
    def __init__(self, pointer: PointerT, /) -> None:
        self.pointer = pointer


class JSONSchemaResolver(ABC, Generic[PointerT]):
    """Resolves the (sub) JSON Schema at the given pointer.

    The implementation of the "pointer" is managed by subclasses.
    """

    def __init__(self, json_schema: dict[str, Any]) -> None:
        self.json_schema = json_schema

    @abstractmethod
    def resolve(self, pointer: PointerT) -> dict[str, Any]:
        pass


class JSONSchemaPointerResolver(JSONSchemaResolver[str]):
    """Resolves the (sub) JSON Schema at the given JSON Pointer, according to RFC 6901."""

    def resolve(self, pointer: str) -> dict[str, Any]:
        # Implementation inspired from the `referencing` library
        schema = self.json_schema
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

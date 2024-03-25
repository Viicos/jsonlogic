from __future__ import annotations

from typing import Any

import pytest

from jsonlogic.json_schema import JSONSchemaDotResolver, JSONSchemaPointerResolver, Unresolvable
from jsonlogic.utils import DataStack


@pytest.mark.parametrize(
    ["schema", "pointer_reference", "dot_reference", "result"],
    [
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            "/a",
            "a",
            {"type": "string"},
        ),
        (
            {"type": "array", "items": {"type": "string"}},
            "/123",
            "123",
            {"type": "string"},
        ),
        (
            {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}}}},
            "/a/321",
            "a.321",
            {"type": "string"},
        ),
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            "/a@0",
            "a@0",
            {"type": "string"},
        ),
    ],
)
def test_resolver_resolve(
    schema: dict[str, Any], pointer_reference: str, dot_reference: str, result: dict[str, Any]
) -> None:
    stack = DataStack(schema)

    pointer_resolver = JSONSchemaPointerResolver(stack)
    assert pointer_resolver.resolve(pointer_reference) == result

    pointer_resolver = JSONSchemaDotResolver(stack)
    assert pointer_resolver.resolve(dot_reference) == result


@pytest.mark.parametrize(
    ["schema", "pointer_reference", "dot_reference"],
    [
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            "/b",
            "b",
        ),
        (
            {"type": "array", "items": {"type": "string"}},
            "/not_an_int",
            "not_an_int",
        ),
        (
            {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}}}},
            "/a/not_an_int",
            "a.not_an_int",
        ),
        ({"type": "object", "properties": {"a": {"type": "string"}}}, "/a/", "a."),
    ],
)
def test_resolver_unresolvable(schema: dict[str, Any], pointer_reference: str, dot_reference: str) -> None:
    stack = DataStack(schema)

    pointer_resolver = JSONSchemaPointerResolver(stack)
    with pytest.raises(Unresolvable):
        pointer_resolver.resolve(pointer_reference)

    pointer_resolver = JSONSchemaDotResolver(stack)
    with pytest.raises(Unresolvable):
        pointer_resolver.resolve(dot_reference)

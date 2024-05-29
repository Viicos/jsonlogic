from __future__ import annotations

from typing import Any

import pytest

from jsonlogic.resolving import (
    DotReferenceParser,
    ParsedReference,
    PointerReferenceParser,
    Unresolvable,
    resolve_data,
    resolve_json_schema,
)
from jsonlogic.typing import JSON

dot_ref_parser = DotReferenceParser()
pointer_ref_parser = PointerReferenceParser()


@pytest.mark.parametrize(
    ["pointer_reference", "dot_reference", "expected"],
    [
        (
            "",
            "",
            ([], 0),
        ),
        (
            "/a",
            "a",
            (["a"], 0),
        ),
        (
            "/123",
            "123",
            (["123"], 0),
        ),
        ("/a/321", "a.321", (["a", "321"], 0)),
        (
            "/a@0",
            "a@0",
            (["a"], 0),
        ),
        (
            "/a/1@3",
            "a.1@3",
            (["a", "1"], 3),
        ),
    ],
)
def test_reference_parser(pointer_reference: str, dot_reference: str, expected: tuple[list[str], int]) -> None:
    parsed_ref, scope = pointer_ref_parser(pointer_reference)
    assert (parsed_ref.segments, scope) == expected

    parsed_ref, scope = dot_ref_parser(dot_reference)
    assert (parsed_ref.segments, scope) == expected


@pytest.mark.parametrize(
    ["pointer_reference", "expected"],
    [
        ("/", ([""], 0)),
        ("//", (["", ""], 0)),
    ],
)
def test_pointer_reference(pointer_reference: str, expected: tuple[list[str], int]) -> None:
    """Pointer references are unambiguous, thus we can parse `"/"` as being `[""]`.

    Note that this is not possible with dot references, so this is tested separately.
    (`""` is special cased to be the root document, and `"."` has to be parsed to `["", ""]`).
    """

    parsed_ref, scope = pointer_ref_parser(pointer_reference)
    assert (parsed_ref.segments, scope) == expected


@pytest.mark.parametrize(
    ["schema", "segments", "expected"],
    [
        (
            {"type": "string"},
            [],
            {"type": "string"},
        ),
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            ["a"],
            {"type": "string"},
        ),
        (
            {"type": "array", "items": {"type": "string"}},
            ["123"],
            {"type": "string"},
        ),
        (
            {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}}}},
            ["a", "321"],
            {"type": "string"},
        ),
    ],
)
def test_resolve_json_schema(schema: dict[str, Any], segments: list[str], expected: dict[str, Any]) -> None:
    assert resolve_json_schema(ParsedReference("", segments), schema) == expected


@pytest.mark.parametrize(
    ["schema", "segments"],
    [
        (
            {"type": "object", "properties": {"a": {"type": "string"}}},
            ["b"],
        ),
        (
            {"type": "array", "items": {"type": "string"}},
            ["not_an_int"],
        ),
        (
            {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "string"}}}},
            ["a", "not_an_int"],
        ),
        ({"type": "object", "properties": {"a": {"type": "string"}}}, ["a", ""]),
    ],
)
def test_resolve_json_schema_unresolvable(schema: dict[str, Any], segments: list[str]) -> None:
    with pytest.raises(Unresolvable):
        resolve_json_schema(ParsedReference("", segments), schema)


@pytest.mark.parametrize(
    ["data", "segments", "expected"],
    [
        ({"a": "test"}, [], {"a": "test"}),
        ({"a": "test"}, ["a"], "test"),
        (["test0", "test1"], ["1"], "test1"),
        ({"a": ["test0"]}, ["a", "0"], "test0"),
    ],
)
def test_resolve_data(data: JSON, segments: list[str], expected: JSON) -> None:
    assert resolve_data(ParsedReference("", segments), data) == expected

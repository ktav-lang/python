"""Independent parameterized insert regressions based on Rust source-mutate09."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "path", "segments", "expected", "semantic"),
    [
        ("a: 1\n", "b", ["b"], "a: 1\nb: 2\n", {"a": 1, "b": 2}),
        ("a: {x: 1}\n", "a.y", ["a", "y"], "a: {x: 1, y: 2}\n", {"a": {"x": 1, "y": 2}}),
        ("{x: 1,}\n", "y", ["y"], "{x: 1, y: 2,}\n", {"x": 1, "y": 2}),
        ("a: {x: 1,   }\n", "a.y", ["a", "y"], "a: {x: 1, y: 2,   }\n", {"a": {"x": 1, "y": 2}}),
        (r"{x: p\,q\\r,   }", "y", ["y"], r"{x: p\,q\\r, y: 2,   }", {"x": "p,q\\r", "y": 2}),
        ("\ufeffa: 1\r\n", "b", ["b"], "\ufeffa: 1\r\nb: 2\r\n", {"a": 1, "b": 2}),
        ("a: 1\nb: 2", "c", ["c"], "a: 1\nb: 2\nc: 2", {"a": 1, "b": 2, "c": 2}),
    ],
)
def test_insert_exact_bytes_and_semantics(
    api: Any, source: str, path: str, segments: list[str], expected: str, semantic: dict[str, Any]
) -> None:
    by_path = api.insert_value(source, path, 2)
    by_segments = api.insert_value_segments(source, segments, 2)
    assert by_path.encode("utf-8") == expected.encode("utf-8")
    assert by_segments.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(by_path) == semantic
    assert api.loads(by_segments) == semantic


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "path", "code"),
    [
        ("a: 1\n", "a", "EditAlreadyExists"),
        ("a: 1\n", "b.c", "EditNotFound"),
        ("a: 1\n", "a..b", "EditInvalidPath"),
    ],
)
def test_insert_error_contract(api: Any, source: str, path: str, code: str) -> None:
    with pytest.raises(api.KtavEditError) as caught:
        api.insert_value(source, path, 2)
    assert caught.value.error == code

"""Exact-byte and independent semantic insert regressions (Rust source-mutate09 oracle)."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "value", "expected", "semantic"),
    [
        ("{a: 1}\n", ["s"], "123", r"{a: 1, s: \u003123}" + "\n", {"a": 1, "s": "123"}),
        ("{a: 1}\n", ["s"], "p,q", r"{a: 1, s: p\,q}" + "\n", {"a": 1, "s": "p,q"}),
        (
            "{a: 1}\n",
            ["s"],
            "back\\slash\nline\r",
            r"{a: 1, s: back\\slash\nline\r}" + "\n",
            {"a": 1, "s": "back\\slash\nline\r"},
        ),
        (r"{x: p\,q\,}" + "\n", ["y"], 2, r"{x: p\,q\,, y: 2}" + "\n", {"x": "p,q,", "y": 2}),
        ('"a.b": {x: 1}\n', ["a.b", "y"], 2, '"a.b": {x: 1, y: 2}\n', {"a.b": {"x": 1, "y": 2}}),
        ("{a: 1,}\n", ["b"], 2, "{a: 1, b: 2,}\n", {"a": 1, "b": 2}),
        ("a: 1\n", ["", "b"], 2, "EditNotFound", None),
        ("## café\na: 1\n", ["b"], 2, "## café\na: 1\nb: 2\n", {"a": 1, "b": 2}),
        ("a: 1\n", ["big"], 9223372036854775807, "a: 1\nbig: 9223372036854775807\n", {"a": 1, "big": 9223372036854775807}),
        ("", ["a", "b"], 1, "EditNotFound", None),
        ("a: {}\n", ["a", "b"], 1, "a: {b: 1}\n", {"a": {"b": 1}}),
        ("", ["a"], 1, "a: 1", {"a": 1}),
        ("a: 1\n", ["a"], 2, "EditAlreadyExists", None),
        ("a: 1\n", ["missing", "child"], 2, "EditNotFound", None),
        ("arr: [1, 2]\n", ["arr", "2"], 3, "EditUnsupported", None),
        ("a: 1\n", [], 2, "EditNotFound", None),
        ("", ["a", "b"], 1, "EditNotFound", None),
    ],
)
def test_insert_exact_and_semantic_oracles(api: Any, source: str, segments: list[str], value: Any, expected: Any, semantic: Any) -> None:
    if semantic is None:
        with pytest.raises(api.KtavEditError) as caught:
            api.insert_value_segments(source, segments, value)
        assert caught.value.error == expected
        return
    actual = api.insert_value_segments(source, segments, value)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
def test_insert_root_comments_preserved_pure(api: Any) -> None:
    source = "## { lead }\n{a: 1}\n## { tail }\n"
    actual = api.insert_value_segments(source, ["b"], 2)
    assert actual.encode("utf-8") == "## { lead }\n{a: 1, b: 2}\n## { tail }\n".encode("utf-8")
    assert api.loads(actual) == {"a": 1, "b": 2}


@pytest.mark.parametrize("api", APIS)
def test_insert_root_leading_comment_pure(api: Any) -> None:
    source = "## only comment\n"
    actual = api.insert_value_segments(source, ["b"], 2)
    assert actual.encode("utf-8") == "## only comment\nb: 2\n".encode("utf-8")
    assert api.loads(actual) == {"b": 2}


@pytest.mark.parametrize("api", APIS)
def test_insert_quoted_dotted_key(api: Any) -> None:
    source = '"a.b": {x: 1}\n'
    expected = '"a.b": {x: 1, y: 2}\n'
    actual = api.insert_value_segments(source, ["a.b", "y"], 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"a.b": {"x": 1, "y": 2}}


@pytest.mark.parametrize("api", APIS)
def test_source_first_insert_keeps_prefix_and_appends(api: Any) -> None:
    source = "## prefix\na: 1\n"
    expected = "## prefix\na: 1\nb: 2\n"
    actual = api.insert_value(source, "b", 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"a": 1, "b": 2}

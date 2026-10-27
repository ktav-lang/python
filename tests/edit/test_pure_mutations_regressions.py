"""Exact-byte and independent semantic remove/rename regression oracles."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "expected", "semantic"),
    [
        (
            "## keep\na: [1, 2, 3]\nb: 4\n",
            ["a", "1"],
            "## keep\na: [1, 3]\nb: 4\n",
            {"a": [1, 3], "b": 4},
        ),
        (
            "root: {child: {leaf: 1}}\nkeep: 2\n",
            ["root", "child", "leaf"],
            "root: {child: {}}\nkeep: 2\n",
            {"root": {"child": {}}, "keep": 2},
        ),
        ('"a.b": {x: 1, y: 2}\n', ["a.b", "x"], '"a.b": {y: 2}\n', {"a.b": {"y": 2}}),
        ("a: 1\nb: 2\n", ["a"], "b: 2\n", {"b": 2}),
    ],
)
def test_remove_exact_bytes_and_semantics(
    api: Any, source: str, segments: list[str], expected: str, semantic: Any
) -> None:
    actual = api.remove_value_segments(source, segments)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "new_key", "expected", "semantic"),
    [
        (
            '"a.b": {x: 1, y: 2}\n',
            ["a.b", "x"],
            "z",
            '"a.b": {z: 1, y: 2}\n',
            {"a.b": {"z": 1, "y": 2}},
        ),
        ('"a.b": 1\n', ["a.b"], "c.d", '"c.d": 1\n', {"c.d": 1}),
        (
            "one: 1\ntwo: 2\nthree: 3\n",
            ["two"],
            "second",
            "one: 1\nsecond: 2\nthree: 3\n",
            {"one": 1, "second": 2, "three": 3},
        ),
        ("a:: 042\n", ["a"], "c.d", '"c.d":: 042\n', {"c.d": "042"}),
    ],
)
def test_rename_exact_bytes_and_semantics(
    api: Any, source: str, segments: list[str], new_key: str, expected: str, semantic: Any
) -> None:
    actual = api.rename_key_segments(source, segments, new_key)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "expected", "semantic"),
    [
        ("## leading\nroot: 1   \nkeep: 2\n", "## leading\nkeep: 2\n", {"keep": 2}),
        (
            "\ufeff## leading\nroot: {child: 1}   \nkeep: 2\n",
            "\ufeff## leading\nkeep: 2\n",
            {"keep": 2},
        ),
    ],
)
def test_remove_inline_root_after_leading_comments_exact_bytes_and_semantics(
    api: Any, source: str, expected: str, semantic: Any
) -> None:
    actual = api.remove_value_segments(source, ["root"])
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
def test_remove_inline_root_after_leading_comments_pure_exact_bytes_and_semantics(api: Any) -> None:
    source = "\ufeff## comment\n {a: 1, b: 2}   \n"
    expected = "\ufeff## comment\n {b: 2}   \n"
    actual = api.remove_value_segments(source, ["a"])
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"b": 2}


@pytest.mark.parametrize("api", APIS)
def test_remove_and_rename_dotted_paths_and_eol(api: Any) -> None:
    source = '"a.b": {child: {leaf: 1}, keep: 2}\r\n'
    actual = api.rename_key_segments(source, ["a.b", "child", "leaf"], "changed")
    expected = '"a.b": {child: {changed: 1}, keep: 2}\r\n'
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"a.b": {"child": {"changed": 1}, "keep": 2}}
    with pytest.raises(api.KtavEditError):
        api.remove_value_segments("a: 1\n", ["missing", "child"])


@pytest.mark.parametrize("api", APIS)
def test_comment_compound_mutations(api: Any) -> None:
    source = "a: {\n  ## note\n  x: 1\n}\n"
    with pytest.raises(api.KtavEditError) as caught:
        api.remove_value_segments(source, ["a"])
    assert caught.value.error == "EditUnsupported"

    with pytest.raises(api.KtavEditError) as caught:
        api.rename_key_segments("a: 1\nb: 2\n", ["a"], "b")
    assert caught.value.error == "EditAlreadyExists"


@pytest.mark.parametrize("api", APIS)
def test_remove_materializes_empty_dotted_parent(api: Any) -> None:
    actual = api.remove_value_segments("a.b: 1\n", ["a", "b"])
    assert actual.encode("utf-8") == b"a: {}\n"
    assert api.loads(actual) == {"a": {}}


@pytest.mark.parametrize("api", APIS)
def test_source_parse_error_precedes_bad_mutation_paths(api: Any) -> None:
    for operation, args in (
        ("remove_value", ("a: {", "a..b")),
        ("rename_key", ("a: {", "a..b", "z")),
        ("remove_value_segments", ("a: {", ["a", ""])),
        ("rename_key_segments", ("a: {", ["a", ""], "z")),
    ):
        with pytest.raises(api.KtavDecodeError) as caught:
            getattr(api, operation)(*args)
        assert caught.value.error == "UnclosedCompound"

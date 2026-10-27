"""Independent source-mutation geometry regressions, matching Rust source-mutate09."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "expected", "semantic"),
    [
        # KTAV whitespace before explicit closer; dotted key and closer bytes survive.
        ("a: {\n\u00a0x: 1\n\u00a0}\n", ["a", "x"], "a: {\n\u00a0}\n", {"a": {}}),
        # Mixed EOLs: nested target is removed without normalizing the LF tail.
        ("a: {\r\n    b: {\r\n        x: 1\r\n    }\r\n}\r\nkeep: 2\ntail: 3\n", ["a", "b", "x"], "a: {\r\n    b: {\r\n    }\r\n}\r\nkeep: 2\ntail: 3\n", {"a": {"b": {}}, "keep": 2, "tail": 3}),
        # Deep dotted deletion materializes only the emptied ancestor chain.
        ("a.b.c: 1\n", ["a", "b", "c"], "a.b: {}\n", {"a": {"b": {}}}),
        ("keep: 0\r\na.b.c: 1", ["a", "b", "c"], "keep: 0\r\na.b: {}", {"keep": 0, "a": {"b": {}}}),
        # Dotted deletion in an NBSP-indented nested block materializes ancestors.
        ("outer: {\n\u00a0a.b.c: 1\n}\n", ["outer", "a", "b", "c"], "outer: {\n\u00a0a.b: {}\n}\n", {"outer": {"a": {"b": {}}}}),
        # Deep dotted deletion materializes through CRLF EOF without adding a final EOL.
        ("a.b.c: 1\r\n", ["a", "b", "c"], "a.b: {}\r\n", {"a": {"b": {}}}),
        ("items: [\r\n  {\r\n    a.b: 1\r\n  }\r\n]\r\n", ["items", "0", "a", "b"], "items: [\r\n  {\r\n    a: {}\r\n  }\r\n]\r\n", {"items": [{"a": {}}]}),
        # Removing final line without EOL keeps EOF unterminated.
        ("keep: 1\nlast: 2", ["last"], "keep: 1", {"keep": 1}),
        # Removing an earlier final-line target preserves the last line and its EOL state.
        ("first: 1\nlast: 2", ["first"], "last: 2", {"last": 2}),
    ],
)
def test_remove_source_geometry_exact_bytes_and_semantics(
    api: Any, source: str, segments: list[str], expected: str, semantic: Any
) -> None:
    actual = api.remove_value_segments(source, segments)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "new_key", "expected", "semantic"),
    [
        # Preserve dotted prefix spelling and intervening whitespace, replace only last segment.
        ('a . b : 1\n', ["a", "b"], "c", 'a . c : 1\n', {"a": {"c": 1}}),
        ('"a.b" . old : 1\n', ["a.b", "old"], "new key", '"a.b" . new key : 1\n', {"a.b": {"new key": 1}}),
        # Rename in place: all surrounding member order and bytes stay stable.
        ("one: 1\ntwo: 2\nthree: 3\n", ["two"], "second", "one: 1\nsecond: 2\nthree: 3\n", {"one": 1, "second": 2, "three": 3}),
    ],
)
def test_rename_source_dotted_segment_geometry(
    api: Any, source: str, segments: list[str], new_key: str, expected: str, semantic: Any
) -> None:
    actual = api.rename_key_segments(source, segments, new_key)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("source", "segments", "value", "expected", "semantic"),
    [
        # Empty explicit root uses the four-space default indentation.
        ("{\n}\n", ["x"], 1, "{\n    x: 1\n}\n", {"x": 1}),
        # Root insertion retains NBSP indentation before the explicit closer.
        ("{\n\u00a0}\n", ["x"], 1, "{\n    x: 1\n\u00a0}\n", {"x": 1}),
        # Mixed EOL nested parent keeps CRLF geometry and the LF-only tail.
        ("root: {\r\n    child: {\r\n    }\r\n}\r\nkeep: 1\ntail: 2\n", ["root", "child", "x"], 1, "root: {\r\n    child: {\r\n        x: 1\r\n    }\r\n}\r\nkeep: 1\ntail: 2\n", {"root": {"child": {"x": 1}}, "keep": 1, "tail": 2}),
    ],
)
def test_insert_source_geometry_materialization(
    api: Any, source: str, segments: list[str], value: Any, expected: str, semantic: Any
) -> None:
    actual = api.insert_value_segments(source, segments, value)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == semantic


@pytest.mark.parametrize("api", APIS)
def test_insert_nested_block_array_object_materialization(api: Any) -> None:
    source = "root: {\n    list: [1]\n}\n"
    expected = "root: {\n    list: [1]\n    child: {\n        value: 2\n    }\n}\n"
    actual = api.insert_value_segments(source, ["root", "child"], {"value": 2})
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"root": {"list": [1], "child": {"value": 2}}}


@pytest.mark.parametrize("api", APIS)
def test_insert_nested_object_inside_array_object(api: Any) -> None:
    source = "items: [{name: one}]\n"
    expected = "items: [{name: one, value: 2}]\n"
    actual = api.insert_value_segments(source, ["items", "0", "value"], 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"items": [{"name": "one", "value": 2}]}


@pytest.mark.parametrize("api", APIS)
def test_mutation_collision_order_and_noop(api: Any) -> None:
    source = "first: 1\nsecond: 2\n"
    assert api.rename_key_segments(source, ["first"], "first").encode("utf-8") == source.encode("utf-8")
    with pytest.raises(api.KtavEditError) as caught:
        api.rename_key_segments(source, ["first"], "second")
    assert caught.value.error == "EditAlreadyExists"
    with pytest.raises(api.KtavEditError) as caught:
        api.insert_value_segments(source, ["second"], 3)
    assert caught.value.error == "EditAlreadyExists"
    actual = api.insert_value_segments(source, ["third"], 3)
    assert actual.encode("utf-8") == b"first: 1\nsecond: 2\nthird: 3\n"
    assert api.loads(actual) == {"first": 1, "second": 2, "third": 3}

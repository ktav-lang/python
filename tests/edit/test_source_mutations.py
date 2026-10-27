"""Source-mutation regression oracles from Rust source-mutate09.

The APIs are expected to be exposed by each backend as insert_value[ _segments],
remove_value[ _segments], and rename_key[ _segments]. Literal segment APIs take
already-decoded Python string sequences (not JSON transport bytes).
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()
ERROR_FIELDS = (
    "error",
    "reason",
    "line",
    "line_text",
    "span",
    "path",
    "body",
    "canonical",
    "spec_section",
    "message",
)


@pytest.mark.parametrize("api", APIS)
def test_insert_text_and_literal_segment_paths(api: Any) -> None:
    source = '"a.b": {old: 1}\na: {b: {x: 2}}\n'
    expected = '"a.b": {old: 1, new: 3}\na: {b: {x: 2}}\n'
    assert api.insert_value(source, r"a\.b.new", 3) == expected
    assert api.insert_value_segments(source, ["a.b", "new"], 3) == expected
    assert api.insert_value("a: 1\n", r"x\.y", 2) == 'a: 1\n"x.y": 2\n'
    assert api.insert_value_segments("a: 1\n", ["x.y"], 2) == 'a: 1\n"x.y": 2\n'
    assert api.insert_value("a: {x: 1}\n", "a.y", "two") == "a: {x: 1, y: two}\n"


@pytest.mark.parametrize("api", APIS)
def test_remove_text_and_literal_segments(api: Any) -> None:
    source = "## keep\na: [1, 2, 3]\nb: 4\n"
    expected = "## keep\na: [1, 3]\nb: 4\n"
    assert api.remove_value(source, "a.1") == expected
    assert api.remove_value_segments(source, ["a", "1"]) == expected
    assert api.remove_value("a: 1\nb: 2\n", "a") == "b: 2\n"
    with pytest.raises(api.KtavEditError) as exc_info:
        api.remove_value_segments("a: 1\n", [])
    assert exc_info.value.error == "EditNotFound"


@pytest.mark.parametrize("api", APIS)
def test_rename_text_and_literal_segments(api: Any) -> None:
    source = '"a.b": {x: 1, y: 2}\na: {b: {x: 3}}\n'
    expected = '"a.b": {z: 1, y: 2}\na: {b: {x: 3}}\n'
    assert api.rename_key(source, r"a\.b.x", "z") == expected
    assert api.rename_key_segments(source, ["a.b", "x"], "z") == expected
    assert api.rename_key("k:: 042\r\n", "k", "k") == "k:: 042\r\n"
    assert api.rename_key_segments("a: {x: 1, y: 2}\n", ["a", "x"], "w") == ("a: {w: 1, y: 2}\n")
    assert api.rename_key("a: 1\n", "a", "ключ") == "ключ: 1\n"


@pytest.mark.parametrize("api", APIS)
def test_mutation_errors_have_typed_edit_contract(api: Any) -> None:
    cases = (
        ("insert_value", ("a: 1\n", "a", 2), "EditAlreadyExists"),
        ("insert_value", ("a: 1\n", "b.c", 2), "EditNotFound"),
        ("remove_value", ("a: 1\n", "missing"), "EditNotFound"),
        ("rename_key", ("a: 1\nb: 2\n", "a", "b"), "EditAlreadyExists"),
    )
    for name, args, code in cases:
        with pytest.raises(api.KtavEditError) as exc_info:
            getattr(api, name)(*args)
        error = exc_info.value
        assert all(hasattr(error, field) for field in ERROR_FIELDS)
        assert error.error == code
        if code == "EditAlreadyExists":
            assert isinstance(error, api.KtavAlreadyExistsError)
        assert isinstance(error.message, str)
        assert error.message
        assert error.reason is None
        assert error.line is None
        assert error.line_text is None
        assert error.span is None
        assert error.path is None
        assert error.canonical is None
        assert error.spec_section is None


@pytest.mark.parametrize("api", APIS)
def test_invalid_text_path_reports_invalid_path(api: Any) -> None:
    with pytest.raises(api.KtavEditError) as exc_info:
        api.insert_value("a: 1\n", "a..b", 2)
    error = exc_info.value
    assert error.error == "EditInvalidPath"
    assert error.body == "2"
    assert error.line is None
    assert error.span is None

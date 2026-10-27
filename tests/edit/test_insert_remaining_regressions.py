"""Insert edge-case regressions cross-checked against Rust source-mutate09."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()


@pytest.mark.parametrize("api", APIS)
def test_insert_source_parse_error_precedes_invalid_path_segments_and_value(api: Any) -> None:
    broken = "a: {"
    with pytest.raises(api.KtavDecodeError) as caught:
        api.insert_value(broken, "a..b", object())
    assert caught.value.error == "UnclosedCompound"
    with pytest.raises(api.KtavDecodeError) as caught:
        api.insert_value_segments(broken, [object()], object())
    assert caught.value.error == "UnclosedCompound"


@pytest.mark.parametrize("api", APIS)
def test_insert_parse_error_offsets_count_utf8_bytes(api: Any) -> None:
    broken = "## café\na: {"
    with pytest.raises(api.KtavDecodeError) as caught:
        api.insert_value(broken, "a.x", 1)
    error = caught.value
    assert error.error == "UnclosedCompound"
    assert error.span == {
        "start": len("## café\na: ".encode("utf-8")),
        "end": len(broken.encode("utf-8")),
    }


@pytest.mark.parametrize("api", APIS)
def test_insert_invalid_path_reports_utf8_byte_offset(api: Any) -> None:
    with pytest.raises(api.KtavInvalidPathError) as caught:
        api.insert_value("a: 1\n", "é..x", 1)
    # parse_path reports the second dot's UTF-8 byte offset: é is two bytes.
    assert caught.value.body == "3"


@pytest.mark.parametrize("api", APIS)
def test_insert_nbsp_whitespace_cases(api: Any) -> None:
    # NBSP is accepted whitespace; inline insertion preserves it after the value.
    source = "{\u00a0}"
    actual = api.insert_value(source, "a", 1)
    assert actual == "{a: 1}"
    assert api.loads(actual) == {"a": 1}


@pytest.mark.parametrize("api", APIS)
def test_insert_structural_trailing_comma_before_nbsp(api: Any) -> None:
    source = "{a: 1,\u00a0}"
    expected = "{a: 1, b: 2,\u00a0}"
    actual = api.insert_value(source, "b", 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(source) == {"a": 1}
    assert api.loads(actual) == {"a": 1, "b": 2}


@pytest.mark.parametrize("api", APIS)
def test_insert_empty_explicit_and_nested_multiline_blocks(api: Any) -> None:
    assert api.insert_value("{\n}\n", "a", 1) == "{\n    a: 1\n}\n"
    source = "outer: {\n  inner: {\n  }\n}\n"
    expected = "outer: {\n  inner: {\n      y: 2\n  }\n}\n"
    actual = api.insert_value_segments(source, ["outer", "inner", "y"], 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"outer": {"inner": {"y": 2}}}


@pytest.mark.parametrize("api", APIS)
def test_insert_array_parent_reports_unsupported(api: Any) -> None:
    with pytest.raises(api.KtavEditError) as caught:
        api.insert_value_segments("items: [1, 2]\n", ["items", "new"], 3)
    assert caught.value.error == "EditUnsupported"


@pytest.mark.parametrize("api", APIS)
def test_insert_existing_key_reports_already_exists(api: Any) -> None:
    with pytest.raises(api.KtavEditError) as caught:
        api.insert_value_segments("a: 1\n", ["a"], 2)
    assert caught.value.error == "EditAlreadyExists"


@pytest.mark.parametrize("api", APIS)
def test_insert_noncontiguous_parent_is_unsupported(api: Any) -> None:
    source = "a.x: 1\na.y: 2\n"
    with pytest.raises(api.KtavEditError) as caught:
        api.insert_value_segments(source, ["a", "z"], 3)
    assert caught.value.error == "EditUnsupported"


@pytest.mark.parametrize("api", APIS)
def test_insert_long_inline_object_expands_for_width(api: Any) -> None:
    value = "x" * 100
    source = "items: { old: 1, keep: [1, 2] }\n"
    actual = api.insert_value_segments(source, ["items", "new"], value)
    assert actual == f"items: {{\n    old: 1\n    keep: [1, 2]\n    new: {value}\n}}\n"
    assert api.loads(actual) == {"items": {"old": 1, "keep": [1, 2], "new": value}}


@pytest.mark.parametrize("api", APIS)
def test_insert_multiline_value_uses_block_form(api: Any) -> None:
    source = "items: { old: 1, keep: [1, 2] }\n"
    value = "first\nsecond"
    actual = api.insert_value_segments(source, ["items", "new"], value)
    assert actual == "items: {\n    old: 1\n    keep: [1, 2]\n    new: ((\nfirst\nsecond\n    ))\n}\n"
    assert api.loads(actual) == {"items": {"old": 1, "keep": [1, 2], "new": value}}


@pytest.mark.parametrize("api", APIS)
def test_insert_inline_root_after_leading_comment_expands_with_trailing_space(api: Any) -> None:
    source = "## leading comment\n{ x: 1 }   \n"
    value = "first\nsecond"
    actual = api.insert_value(source, "y", value)
    expected = "## leading comment\n{\n    x: 1\n    y: ((\nfirst\nsecond\n    ))\n}   \n"
    assert actual == expected
    assert api.loads(actual) == {"x": 1, "y": value}


@pytest.mark.parametrize("api", APIS)
def test_insert_leading_comments_braces_and_whitespace(api: Any) -> None:
    source = "## { leading }\n  { x: 1,   }  \n## tail\n"
    expected = "## { leading }\n  { x: 1, y: 2,   }  \n## tail\n"
    actual = api.insert_value(source, "y", 2)
    assert actual.encode("utf-8") == expected.encode("utf-8")
    assert api.loads(actual) == {"x": 1, "y": 2}

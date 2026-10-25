"""``edit_value`` / ``edit_value_segments``: lossless source-value edits.

Port of the Rust reference suite ``tests/suite/api/text/edit_value.rs``
(maintained here as literal-output oracles: a test proves the bytes
outside the target were not touched). Every case runs on the pure
backend and — when the extension exposes the 0.9 symbols — on the
native backend with identical oracles.
"""

from __future__ import annotations

from typing import Any

import ktav.pure as pure
import pytest
from tests.edit._backends import edit_apis

APIS = edit_apis()


def _unwrap(exc: pytest.ExceptionInfo[Any]) -> Any:
    return exc.value


@pytest.mark.parametrize("api", APIS)
def test_string_replacement_plain(api: Any) -> None:
    assert api.edit_value("port: 8080\nhost: db\n", "port", "db.internal") == (
        "port: db.internal\nhost: db\n"
    )


@pytest.mark.parametrize("api", APIS)
def test_int_replacement_switches_raw_marker_off(api: Any) -> None:
    # `:: 8080` was a String; an Integer replacement must switch it off.
    assert api.edit_value("port:: 8080\n", "port", 9090) == "port: 9090\n"


@pytest.mark.parametrize("api", APIS)
def test_numeric_string_replacement_switches_raw_marker_on(api: Any) -> None:
    assert api.edit_value("port: 8080\n", "port", "42") == "port:: 42\n"


@pytest.mark.parametrize("api", APIS)
def test_keyword_like_string_replacement_needs_raw(api: Any) -> None:
    assert api.edit_value("mode: auto\n", "mode", "true") == "mode:: true\n"


@pytest.mark.parametrize("api", APIS)
def test_raw_marker_preserved_for_string(api: Any) -> None:
    assert api.edit_value("k:: v1\n", "k", "v2") == "k:: v2\n"


@pytest.mark.parametrize("api", APIS)
def test_empty_string_replacement_keeps_raw(api: Any) -> None:
    assert api.edit_value("k:: x\n", "k", "") == "k:: \n"


@pytest.mark.parametrize("api", APIS)
def test_null_and_bool_replacements(api: Any) -> None:
    t = "a: x\nb: y\nc: z\n"
    assert api.edit_value(t, "a", None) == "a: null\nb: y\nc: z\n"
    assert api.edit_value(t, "b", False) == "a: x\nb: false\nc: z\n"
    assert api.edit_value(t, "c", True) == "a: x\nb: y\nc: true\n"


@pytest.mark.parametrize("api", APIS)
def test_float_replacement(api: Any) -> None:
    assert api.edit_value("ratio: 1\n", "ratio", 0.5) == "ratio: 0.5\n"


@pytest.mark.parametrize("api", APIS)
def test_nested_dotted_path(api: Any) -> None:
    t = "srv: {\n  host: a\n  port: 1\n}\n"
    assert api.edit_value(t, "srv.host", "b.example") == (
        "srv: {\n  host: b.example\n  port: 1\n}\n"
    )


@pytest.mark.parametrize("api", APIS)
def test_dotted_source_key_leaf(api: Any) -> None:
    assert api.edit_value("a.b: 1\nc: 2\n", "a.b", 3) == "a.b: 3\nc: 2\n"


@pytest.mark.parametrize("api", APIS)
def test_array_index_replacement(api: Any) -> None:
    t = "list: [\n  one\n  two\n]\n"
    assert api.edit_value(t, "list.1", "TWO") == "list: [\n  one\n  TWO\n]\n"


@pytest.mark.parametrize("api", APIS)
def test_numeric_segment_is_string_key_in_object(api: Any) -> None:
    t = "0: first\nlist: [\n  x\n]\n"
    assert api.edit_value(t, "0", "zero") == "0: zero\nlist: [\n  x\n]\n"
    assert api.edit_value(t, "list.0", "y") == "0: first\nlist: [\n  y\n]\n"


@pytest.mark.parametrize("api", APIS)
def test_escaped_dot_in_path_vs_real_key(api: Any) -> None:
    t = '"a.b": 1\na: {\n  b: 2\n}\n'
    assert api.edit_value(t, "a\\.b", 9) == '"a.b": 9\na: {\n  b: 2\n}\n'
    assert api.edit_value(t, "a.b", 9) == '"a.b": 1\na: {\n  b: 9\n}\n'


@pytest.mark.parametrize("api", APIS)
def test_escaped_backslash_in_path(api: Any) -> None:
    t = '"a\\\\b": 1\n'
    assert api.edit_value(t, "a\\\\b", 2) == '"a\\\\b": 2\n'


@pytest.mark.parametrize("api", APIS)
def test_segments_api_equivalent(api: Any) -> None:
    t = "a: {\n  b: 1\n}\n"
    assert api.edit_value_segments(t, ["a", "b"], 2) == "a: {\n  b: 2\n}\n"


@pytest.mark.parametrize("api", APIS)
def test_inline_pair_byte_exact(api: Any) -> None:
    assert api.edit_value("a: {x: 1, y: 2}\n", "a.y", 3) == "a: {x: 1, y: 3}\n"


@pytest.mark.parametrize("api", APIS)
def test_inline_raw_pair(api: Any) -> None:
    assert api.edit_value("a: {k:: v, j: w}\n", "a.k", "z") == "a: {k:: z, j: w}\n"


@pytest.mark.parametrize("api", APIS)
def test_inline_nonempty_compound_replacement_inline_exact(api: Any) -> None:
    assert api.edit_value("a: {x:1}\n", "a.x", {"n": 1}) == "a: {x:{n: 1}}\n"


@pytest.mark.parametrize("api", APIS)
def test_inline_nested_compound_replacement(api: Any) -> None:
    assert api.edit_value("a: {x: 1}\n", "a.x", {"n": [{"m": 2}]}) == ("a: {x: {n: [{m: 2}]}}\n")


@pytest.mark.parametrize("api", APIS)
def test_scalar_to_compound(api: Any) -> None:
    assert api.edit_value("a: 1\n", "a", {"x": 1}) == "a: {\n    x: 1\n}\n"


@pytest.mark.parametrize("api", APIS)
def test_empty_compound_to_filled(api: Any) -> None:
    assert api.edit_value("a: {}\nb: 2\n", "a", {"x": 1}) == "a: {x: 1}\nb: 2\n"


@pytest.mark.parametrize("api", APIS)
def test_compound_to_scalar(api: Any) -> None:
    assert api.edit_value("a: {\n  x: 1\n}\n", "a", 5) == "a: 5\n"


@pytest.mark.parametrize("api", APIS)
def test_reopen_leaf_editable_whole_target_unsupported(api: Any) -> None:
    t = "a: {}\na.y: 2\n"
    assert api.edit_value(t, "a.y", 3) == "a: {}\na.y: 3\n"
    with pytest.raises(api.KtavUnsupportedError):
        api.edit_value(t, "a", 9)


@pytest.mark.parametrize("api", APIS)
def test_multiline_string_replacement(api: Any) -> None:
    assert api.edit_value("s: (\n hi\n)\n", "s", "a\nb") == "s: ((\na\nb\n))\n"


@pytest.mark.parametrize("api", APIS)
def test_multiline_string_with_terminator_line_unsupported(api: Any) -> None:
    with pytest.raises(api.KtavUnsupportedError):
        api.edit_value("s: (\n hi\n)\n", "s", "x\n))\ny")


@pytest.mark.parametrize("api", APIS)
def test_comments_blanks_and_trailing_bytes_preserved(api: Any) -> None:
    t = "## top\n\na: 1\n\n## end\n"
    assert api.edit_value(t, "a", 2) == "## top\n\na: 2\n\n## end\n"


@pytest.mark.parametrize("api", APIS)
def test_crlf_document_preserved(api: Any) -> None:
    t = "a: 1\r\nb: two\r\n"
    assert api.edit_value(t, "b", "three") == "a: 1\r\nb: three\r\n"


@pytest.mark.parametrize("api", APIS)
def test_cr_only_document_preserved(api: Any) -> None:
    t = "a: 1\rb: two\r"
    assert api.edit_value(t, "b", "three") == "a: 1\rb: three\r"


@pytest.mark.parametrize("api", APIS)
def test_bom_and_no_final_newline_preserved(api: Any) -> None:
    t = "﻿a: 1"
    assert api.edit_value(t, "a", 2) == "﻿a: 2"


@pytest.mark.parametrize("api", APIS)
def test_utf8_values_and_keys(api: Any) -> None:
    assert api.edit_value("ключ: значение\n", "ключ", "число") == "ключ: число\n"


@pytest.mark.parametrize("api", APIS)
def test_not_found_cases(api: Any) -> None:
    t = "a: {\n  b: 1\n}\nlist: [\n  x\n]\n"
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value(t, "missing", "v")
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value(t, "a.b.c", "v")
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value(t, "list.5", "v")
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value(t, "a.b.c.d", "v")
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value("a: scalar\n", "a.b", "v")
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value_segments(t, [], "v")


@pytest.mark.parametrize("api", APIS)
def test_invalid_path_cases(api: Any) -> None:
    t = "a: 1\n"
    for path, offset in (
        ("a\\nb", 1),
        ("a\\", 1),
        ("", 0),
        ("a..b", 2),
        (".a", 0),
    ):
        with pytest.raises(api.KtavInvalidPathError) as exc_info:
            api.edit_value(t, path, "v")
        assert exc_info.value.body == str(offset), path
        assert exc_info.value.error == "EditInvalidPath"
        assert exc_info.value.line is None
        assert exc_info.value.span is None


@pytest.mark.parametrize("api", APIS)
def test_non_numeric_index_in_array_is_not_found(api: Any) -> None:
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value_segments("list: [\n  x\n]\n", ["list", "abc"], "v")


@pytest.mark.parametrize("api", APIS)
def test_leading_zero_index_addresses_the_same_item(api: Any) -> None:
    assert api.edit_value("list: [\n  one\n  two\n]\n", "list.01", "TWO") == (
        "list: [\n  one\n  TWO\n]\n"
    )


@pytest.mark.parametrize("api", APIS)
def test_signed_index_is_not_found(api: Any) -> None:
    with pytest.raises(api.KtavNotFoundError):
        api.edit_value_segments("list: [\n  x\n]\n", ["list", "-1"], "v")


@pytest.mark.parametrize("api", APIS)
def test_malformed_source_raises_the_real_source_error(api: Any) -> None:
    """0.9 source-first priority: the parser envelope wins over EditUnsupported.

    Both edit entry points validate + parse the source BEFORE the path /
    replacement transport decode, so a malformed source carries real
    coordinates (line/line_text/span) — never a coordinate-less
    edit error.
    """
    broken = "a: {\n  x: 1\n"
    with pytest.raises(api.KtavDecodeError) as exc_info:
        api.edit_value(broken, "a.x", "v")
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert e.line == 1
    assert isinstance(e.span, dict)
    assert e.span["end"] > e.span["start"]
    with pytest.raises(api.KtavDecodeError) as seg_exc:
        api.edit_value_segments(broken, ["a", "x"], "v")
    assert seg_exc.value.error == "UnclosedCompound"


@pytest.mark.parametrize("api", APIS)
def test_source_error_beats_path_and_replacement_errors(api: Any) -> None:
    broken = "a: {"
    # A bad path on an unparseable source still reports the source.
    with pytest.raises(api.KtavDecodeError):
        api.edit_value(broken, "a\\nb", "v")
    # An unencodable replacement never masks the source error either.
    with pytest.raises(api.KtavDecodeError):
        api.edit_value(broken, "a", object())


@pytest.mark.parametrize("api", APIS)
def test_patched_documents_reparse(api: Any) -> None:
    out = api.edit_value("port: 8080\n", "port", 9090)
    assert pure.loads(out) == {"port": 9090}
    out = api.edit_value("list: [\n  one\n]\n", "list.0", "two")
    assert pure.loads(out) == {"list": ["two"]}


@pytest.mark.parametrize("api", APIS)
def test_pair_spacing_and_eol_preserved(api: Any) -> None:
    t = "  a:\t   old  \r\n"
    assert api.edit_value(t, "a", "new") == "  a:\t   new  \r\n"


@pytest.mark.parametrize("api", APIS)
def test_int_after_raw_drops_only_extra_colon(api: Any) -> None:
    assert api.edit_value("k::  8080\n", "k", 9090) == "k:  9090\n"


@pytest.mark.parametrize("api", APIS)
def test_same_value_no_op_is_byte_identical(api: Any) -> None:
    t = "a: x\n"
    assert api.edit_value(t, "a", "x") == t


@pytest.mark.parametrize("api", APIS)
def test_noop_distinguishes_int_from_bool(api: Any) -> None:
    """True == 1 in Python; the edit engine must NOT treat them as equal.

    Oracle per the Rust reference suite: a Bool replacement stays a
    plain bare scalar (`a: true`) — the raw `::` marker is reserved for
    String provenance, and a raw marker here would re-parse as String.
    """
    assert api.edit_value("a: 1\n", "a", True) == "a: true\n"


@pytest.mark.parametrize("api", APIS)
def test_signed_zero_flip_is_a_real_edit(api: Any) -> None:
    """Float equality must preserve signed zero.

    The native core keeps Value::Float as canonical text, where `-0.0`
    and `0.0` differ; the pure engine must agree, so a zero sign flip
    performs a real splice in both directions instead of a no-op.
    """
    assert api.edit_value("n: -0.0\n", "n", 0.0) == "n: 0.0\n"
    assert api.edit_value("n: 0.0\n", "n", -0.0) == "n: -0.0\n"
    assert api.edit_value_segments("n: -0.0\n", ["n"], 0.0) == "n: 0.0\n"
    assert api.edit_value_segments("n: 0.0\n", ["n"], -0.0) == "n: -0.0\n"


@pytest.mark.parametrize("api", APIS)
def test_same_sign_zero_noop_keeps_noncanonical_spelling(api: Any) -> None:
    for source in ("n: 0.00\n", "n: -0.00\n"):
        replacement = -0.0 if source.startswith("n: -") else 0.0
        assert api.edit_value(source, "n", replacement) == source, source
        assert api.edit_value_segments(source, ["n"], replacement) == source


@pytest.mark.parametrize("api", APIS)
def test_empty_body_pair_replacement(api: Any) -> None:
    t = "k: \n"
    assert api.edit_value(t, "k", "x") == "k: x \n"
    assert api.edit_value(t, "k", "") == "k: \n"


@pytest.mark.parametrize("api", APIS)
def test_compound_with_internal_comments_structural_replacement_rejected(api: Any) -> None:
    t = "a: {\n  ## inner\n  x: 1\n}\n"
    with pytest.raises(api.KtavUnsupportedError):
        api.edit_value(t, "a", {"y": 2})


@pytest.mark.parametrize("api", APIS)
def test_leaf_inside_commented_container_edits_and_keeps_comments(api: Any) -> None:
    t = "a: {\n  ## inner\n  x: 1\n}\n"
    assert api.edit_value(t, "a.x", 2) == "a: {\n  ## inner\n  x: 2\n}\n"


@pytest.mark.parametrize("api", APIS)
def test_hash_hash_inside_multiline_string_is_data_not_comment(api: Any) -> None:
    t = "a: {\n  s: (\n    ## not comment\n  )\n}\n"
    assert api.edit_value(t, "a", 7) == "a: 7\n"


@pytest.mark.parametrize("api", APIS)
def test_implicit_root_array_first_item_pair_shaped_gets_raw(api: Any) -> None:
    t = ":: old\nsecond\n"
    assert api.edit_value(t, "0", "a: b") == ":: a: b\nsecond\n"


@pytest.mark.parametrize("api", APIS)
def test_implicit_root_array_second_item_bare_ok(api: Any) -> None:
    t = ":: old\nsecond\n"
    assert api.edit_value(t, "1", "a: b") == ":: old\na: b\n"


@pytest.mark.parametrize("api", APIS)
def test_explicit_root_array_first_item_raw_preserved(api: Any) -> None:
    t = "[\n  :: old\n  x\n]\n"
    assert api.edit_value(t, "0", "k: v") == "[\n  :: k: v\n  x\n]\n"


@pytest.mark.parametrize("api", APIS)
def test_root_inline_object_child(api: Any) -> None:
    assert api.edit_value("{x: 1}\n", "x", 2) == "{x: 2}\n"


@pytest.mark.parametrize("api", APIS)
def test_integer_precision_is_never_coerced_to_float(api: Any) -> None:
    # 2**53 + 1 is exactly representable in i64 but NOT in f64: the edit
    # must keep it an exact integer literal, never a float spelling.
    big = 9007199254740993  # 2**53 + 1
    out = api.edit_value("n: 1\n", "n", big)
    assert out == f"n: {big}\n"
    parsed = pure.loads(out)["n"]
    assert parsed == big
    assert isinstance(parsed, int) and not isinstance(parsed, bool)
    # The float spelling would round-trip to a different value.
    assert f"{big}.0" not in out and "e" not in out.lower()


@pytest.mark.parametrize("api", APIS)
def test_source_is_never_mutated(api: Any) -> None:
    t = "a: 1\nb: 2\n"
    api.edit_value(t, "a", 99)
    assert t == "a: 1\nb: 2\n"


def test_edit_error_envelope_shape() -> None:
    with pytest.raises(pure.KtavEditError) as unsupported:
        pure.edit_value("a: {}\na.y: 2\n", "a", 9)
    e = unsupported.value
    for field in (
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
    ):
        assert hasattr(e, field)
    assert e.error == "EditUnsupported"
    assert e.reason is None
    assert e.line is None
    assert e.span is None
    assert isinstance(e.body, str)  # the limitation reason
    assert e.body  # nonempty
    assert str(e).startswith("no lossless source edit: ")
    with pytest.raises(pure.KtavNotFoundError) as not_found:
        pure.edit_value("a: 1\n", "zzz", 1)
    assert not_found.value.error == "EditNotFound"
    assert not_found.value.body is None


def test_unsupported_replacement_type_is_a_message_envelope() -> None:
    with pytest.raises(pure.KtavEncodeError) as exc_info:
        pure.edit_value("a: 1\n", "a", object())
    assert exc_info.value.error == "Message"

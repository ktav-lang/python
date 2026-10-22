"""Pure-backend-only units that the parametrized conformance runner does
not already cover per backend.

The five spec-corpus categories (valid/invalid/unrepresentable/
parseable-unrepresentable/strict-lossy) run for BOTH backends —
including ktav.pure — in ``tests/test_conformance.py``; nothing here
duplicates them. What the runner cannot express lives here: documents
whose interesting behaviour only shows up in the pure byte-level entry
points, and empty/comment-only roots (mirroring the ``valid/empty``
corpus oracles, which pin empty input to an empty Object root with an
empty canonical form).
"""

from __future__ import annotations

import io
import math

import pytest
from ktav import pure


def test_empty_and_comment_only_documents_are_empty_objects() -> None:
    """The corpus oracle for valid/empty/* pins all three spellings to an
    empty Object root with an EMPTY canonical form (no scalar root, no
    error): empty input, comment-only input, whitespace-only input."""
    for source in ("", "## only a comment\n", "   \n\t\n"):
        assert pure.loads(source) == {}
        assert pure.emit_canonical(pure.loads(source)) == ""
        assert pure.canonical_from_source(source) == ""


def test_bom_is_stripped_not_key_content() -> None:
    assert pure.loads("﻿host: value") == {"host": "value"}


def test_crlf_and_lone_cr_are_line_terminators() -> None:
    assert pure.loads("a: 1\r\nb: 2\r\n") == {"a": 1, "b": 2}
    assert pure.loads("a: 1\rb: 2") == {"a": 1, "b": 2}


def test_original_line_endings_are_not_required_for_semantics() -> None:
    """Mixed endings in one document (§ 3.2) parse as one document."""
    assert pure.loads("a: 1\nb: 2\r\nc: 3\r") == {"a": 1, "b": 2, "c": 3}


def test_bytes_entry_point_round_trip() -> None:
    """`loads` accepts UTF-8 bytes; valid bytes must behave like text."""
    assert pure.loads(b"a: 1\n") == {"a": 1}
    assert pure.loads(bytearray(b"a: 1\n")) == {"a": 1}


def test_invalid_utf8_rejected_before_grammar() -> None:
    """§ 6.15: malformed bytes fail with InvalidUtf8 even when the text
    around them is also grammatically broken — UTF-8 validity comes first."""
    raw = b"{{{not even grammar \xed\xa0\x80"
    with pytest.raises(pure.KtavDecodeError) as excinfo:
        pure.loads(raw)
    error = excinfo.value
    assert error.error == "InvalidUtf8"
    assert error.spec_section == "§6.15"
    assert error.span is not None
    assert error.span["end"] > error.span["start"]
    assert error.span["end"] - error.span["start"] >= 1


def test_depth_limit_is_an_envelope_error_not_recursionerror() -> None:
    """A 200-deep inline array exceeds the declared inline-depth limit
    (128): it must surface as the documented KtavDecodeError, never as a
    Python RecursionError. (Pure-parser internal limit, mirrored 1:1 from
    the Rust core.)"""
    source = "[" * 200 + "]" * 200
    # pytest.raises(KtavDecodeError) itself fails if a RecursionError
    # escapes instead — the depth limit must hold in either case.
    with pytest.raises(pure.KtavDecodeError) as excinfo:
        pure.loads(source)
    assert excinfo.value.error == "MalformedInlineCompound"
    assert "depth" in excinfo.value.message


def test_integers_beyond_i64_fall_back_to_string() -> None:
    """Corpus normative (valid/numbers/integer/big_overflow_to_string):
    integer literals past the i64 domain are Strings, re-emitted via the
    raw marker so they stay strings."""
    value = pure.loads("n: 99999999999999999999\n")
    assert value == {"n": "99999999999999999999"}
    assert isinstance(value["n"], str)
    assert pure.emit_canonical(value) == "n:: 99999999999999999999\n"
    assert pure.loads(pure.dumps(value)) == value


def test_negative_zero_is_preserved() -> None:
    value = pure.loads("z: -0.0\n")["z"]
    assert value == 0.0
    assert math.copysign(1.0, value) == -1.0
    assert pure.emit_canonical({"z": value}) == "z: -0.0\n"


def test_dump_file_wrapper_writes_utf8_in_binary_mode() -> None:
    out = io.BytesIO()
    pure.dump({"ключ": "значение"}, out)
    assert out.getvalue() == "ключ: значение\n".encode()

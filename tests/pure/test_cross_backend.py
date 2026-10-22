"""Native ↔ pure cross-backend contracts.

Round trips BOTH directions, canonical byte equality between backends,
strict-lossy envelope field-by-field equality, and — crucially —
NEGATIVE CONTROLS whose expected values are INDEPENDENT: hand-written
canonical strings and hand-written parse results, never derived from
either implementation, so two equally wrong backends cannot pass by
agreeing.

The cross-backend tests need the native backend and are skipped when it
is absent (the pure-mode CI job runs the single-backend conformance
runner instead); the regular ``test`` job fails via tests/conftest.py
if the native extension ever goes missing there.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import ktav
import pytest
from ktav import pure

import tests.conformance_runner as cr

NEEDS_NATIVE = pytest.mark.skipif(
    not ktav._HAS_CORE, reason="cross-backend contracts need the native backend"
)


def both() -> list[Any]:
    return cr.BACKENDS


# ---------------------------------------------------------------------------
# Synthetic documents with HAND-WRITTEN oracles.
# Each entry: (id, source, expected parsed value, expected canonical or
# None when the canonical spelling is not independently pinned here).
# ---------------------------------------------------------------------------

SYNTHETIC_DOCS = [
    pytest.param(
        "v: {a: {b: 1}}",
        {"v": {"a": {"b": 1}}},
        "v: {\n    a: {\n        b: 1\n    }\n}\n",
        id="nested-inline",
    ),
    pytest.param(
        "v: {\n    a: {\n        b: 1\n    }\n}",
        {"v": {"a": {"b": 1}}},
        "v: {\n    a: {\n        b: 1\n    }\n}\n",
        id="nested-multiline",
    ),
    pytest.param(
        "a.b: 1\nc: 2\na.d: 3",
        {"a": {"b": 1, "d": 3}, "c": 2},
        "a: {\n    b: 1\n    d: 3\n}\nc: 2\n",
        id="dotted-reopen-merge",
    ),
    pytest.param(
        '"say \\"hi\\"": 1',
        {'say "hi"': 1},
        'say "hi": 1\n',
        id="quoted-key-escapes",
    ),
    pytest.param(
        # § 3.7.1: \uXXXX escapes decode ONLY inside inline compounds and
        # keys. A surrogate pair in a REAL inline context decodes to the
        # astral character.
        "{s: \\ud83d\\ude00}",
        {"s": "\U0001f600"},
        None,  # non-ASCII canonical spelling is pinned by the spec corpus
        id="surrogate-pair-valid",
    ),
    pytest.param(
        # ... while a BARE line scalar keeps the six bytes literal.
        "s: \\ud800",
        {"s": "\\ud800"},
        "s: \\ud800\n",  # backslash stays a backslash; plain `: ` spelling
        id="surrogate-escape-bare-line-stays-literal",
    ),
    pytest.param(
        "ver: 01.5",
        {"ver": "01.5"},
        "ver:: 01.5\n",
        id="leading-zero-float-is-string",
    ),
    pytest.param(
        "hex_upper: 0xFF\nhex_lower: 0xff\nbool_True: True",
        {"hex_upper": 255, "hex_lower": 255, "bool_True": "True"},
        "hex_upper: 255\nhex_lower: 255\nbool_True: True\n",
        id="prefix-case",
    ),
    pytest.param(
        "z: -0.0",
        {"z": -0.0},
        "z: -0.0\n",
        id="negative-zero-float",
    ),
    pytest.param(
        # Spec normative (corpus big_overflow_to_string): integer literals
        # beyond the i64 domain fall back to String.
        "n: 99999999999999999999",
        {"n": "99999999999999999999"},
        "n:: 99999999999999999999\n",
        id="big-int-beyond-2e53",
    ),
    pytest.param(
        "﻿host: value",
        {"host": "value"},
        "host: value\n",
        id="bom",
    ),
    pytest.param(
        "a: 1\r\nb: 2\r\n",
        {"a": 1, "b": 2},
        "a: 1\nb: 2\n",
        id="crlf",
    ),
    pytest.param(
        "a: 1\rb: 2",
        {"a": 1, "b": 2},
        "a: 1\nb: 2\n",
        id="lone-cr",
    ),
    pytest.param(
        "",
        {},
        "",
        id="empty-root",
    ),
    pytest.param(
        "## just a comment\n",
        {},
        "",
        id="comment-only-root",
    ),
]

# Documents that BOTH backends must REJECT with the named envelope
# category (hand-picked per parser state/boundary, not corpus-derived).
# The unpaired-surrogate cases use a REAL inline context: § 3.7.1 decodes
# escapes only inside inline compounds/keys, so that is where a stray
# surrogate is actually rejected (a bare line keeps the bytes literal).
SYNTHETIC_REJECTIONS = [
    pytest.param("a: 1\na: 2\n", "DuplicateKey", id="duplicate-key"),
    pytest.param("a: 1\na.b: 2\n", "KeyPathConflict", id="key-path-conflict"),
    pytest.param("{s: \\ud83d}", "BadEscapeSequence", id="unpaired-high-surrogate"),
    pytest.param("{s: \\udc00}", "BadEscapeSequence", id="unpaired-low-surrogate"),
    pytest.param(
        "[" * 200 + "]" * 200,
        "MalformedInlineCompound",
        id="depth-beyond-limit",
    ),
]


@pytest.mark.parametrize("be", both())
@pytest.mark.parametrize(("source", "expected", "canonical"), SYNTHETIC_DOCS)
def test_synthetic_doc_matches_independent_oracles(
    be: cr.Backend, source: str, expected: Any, canonical: str | None
) -> None:
    assert be.api.loads(source) == expected
    if canonical is not None:
        assert be.api.emit_canonical(be.api.loads(source)) == canonical


@pytest.mark.parametrize("be", both())
@pytest.mark.parametrize(("source", "expected_category"), SYNTHETIC_REJECTIONS)
def test_synthetic_rejections_are_envelope_errors(
    be: cr.Backend, source: str, expected_category: str
) -> None:
    with pytest.raises(be.api.KtavDecodeError) as exc_info:
        be.api.loads(source)
    assert exc_info.value.error == expected_category


def test_depth_limit_is_not_recursionerror() -> None:
    for be in cr.available_backends():
        with pytest.raises(be.api.KtavDecodeError):
            be.api.loads("[" * 200 + "]" * 200)


# ---------------------------------------------------------------------------
# Writer rejections (both backends, § 5.9.0)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("be", both())
def test_scalar_root_writer_rejection(be: cr.Backend) -> None:
    for value in (42, 4.2, "text", True, None):
        for dump in (be.api.dumps, be.api.emit_canonical):
            with pytest.raises(be.api.KtavEncodeError) as exc_info:
                dump(value)
            assert exc_info.value.reason == "ScalarRoot"


@pytest.mark.parametrize("be", both())
def test_non_finite_float_writer_rejection(be: cr.Backend) -> None:
    for value in (float("nan"), float("inf"), float("-inf")):
        for dump in (be.api.dumps, be.api.emit_canonical):
            with pytest.raises(be.api.KtavEncodeError) as exc_info:
                dump({"v": value})
            assert exc_info.value.reason == "NonFiniteFloat"


@pytest.mark.parametrize("be", both())
def test_force_strings_coercion_round_trips_as_strings(be: cr.Backend) -> None:
    out = be.api.dumps_force_strings({"p": 8080, "r": 0.5, "o": {"k": 1}, "a": [2, True, None]})
    back = be.api.loads(out)
    assert back == {"p": "8080", "r": "0.5", "o": {"k": "1"}, "a": ["2", "true", "null"]}
    # ... and the output of one backend reparses on the other:
    assert be.api.loads(be.api.dumps_force_strings(back)) == back


# ---------------------------------------------------------------------------
# Cross-backend round trips over the full valid corpus (native required)
# ---------------------------------------------------------------------------


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_native_parse_pure_write_native_read(ktav_file: Path, json_file: Path) -> None:
    cr.skip_if_missing(cr.VALID_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    text = cr._fixture_text(ktav_file)
    mid = ktav.pure.dumps(ktav.loads(text))
    assert ktav.loads(mid) == oracle
    assert ktav.pure.loads(mid) == oracle


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_pure_parse_native_write_pure_read(ktav_file: Path, json_file: Path) -> None:
    cr.skip_if_missing(cr.VALID_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    text = cr._fixture_text(ktav_file)
    mid = ktav.dumps(ktav.pure.loads(text))
    assert ktav.pure.loads(mid) == oracle
    assert ktav.loads(mid) == oracle


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_canonical_bytes_are_identical_between_backends(ktav_file: Path, json_file: Path) -> None:
    cr.skip_if_missing(cr.VALID_DIR)
    text = cr._fixture_text(ktav_file)
    assert ktav.emit_canonical(ktav.loads(text)) == ktav.pure.emit_canonical(ktav.pure.loads(text))


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_format_output_is_identical_between_backends(ktav_file: Path, json_file: Path) -> None:
    cr.skip_if_missing(cr.VALID_DIR)
    text = cr._fixture_text(ktav_file)
    assert ktav.format(text) == ktav.pure.format(text)


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.strict_lossy_cases()))
def test_strict_lossy_envelopes_match_field_by_field(ktav_file: Path, json_file: Path) -> None:
    """All ten envelope fields must agree between backends on every
    strict-lossy fixture — same category, same body, same canonical, same
    byte spans, same message."""
    cr.skip_if_missing(cr.STRICT_LOSSY_DIR)
    text = cr._fixture_text(ktav_file)
    with pytest.raises(ktav.KtavDecodeError) as native_exc:
        ktav.loads_strict(text)
    with pytest.raises(ktav.pure.KtavDecodeError) as pure_exc:
        ktav.pure.loads_strict(text)
    native, pure_error = native_exc.value, pure_exc.value
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
        assert getattr(native, field) == getattr(pure_error, field), f"field {field} differs"


@NEEDS_NATIVE
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.strict_lossy_cases()))
def test_strict_lossy_lax_values_match_between_backends(ktav_file: Path, json_file: Path) -> None:
    cr.skip_if_missing(cr.STRICT_LOSSY_DIR)
    text = cr._fixture_text(ktav_file)
    assert ktav.loads(text) == ktav.pure.loads(text)


def test_negative_zero_sign_is_identical_between_backends() -> None:
    for be in cr.available_backends():
        value = be.api.loads("z: -0.0\n")["z"]
        assert value == 0.0
        assert math.copysign(1.0, value) == -1.0


# ---------------------------------------------------------------------------
# Writer § 5.9.0/§ 5.9.7 rejections with the DECODED OBJECT-KEY path.
#
# Verified against rust/src/document/render/representable.rs: array items
# push NO path segment (check_node recurses without touching `path`), the
# offending pair's key is pushed verbatim BEFORE the empty-key check (so
# EmptyKeyName ends with the empty string, never split on dots), and only
# the binding-level NonFiniteFloat guard stays pathless (`Unrepresentable`).
# Every assertion below checks all ten envelope fields.
# ---------------------------------------------------------------------------


_ERROR_FIELDS = (
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


def _assert_encode_rejection(be: cr.Backend, value: Any, expected: dict[str, Any]) -> None:
    for dump in (be.api.dumps, be.api.emit_canonical):
        with pytest.raises(be.api.KtavEncodeError) as exc_info:
            dump(value)
        error = exc_info.value
        for field in _ERROR_FIELDS:
            assert hasattr(error, field), f"missing envelope field {field}"
        for field, expected_value in expected.items():
            assert getattr(error, field) == expected_value, f"field {field} differs"


@pytest.mark.parametrize("be", both())
def test_cr_byte_rejection_carries_the_object_key_path(be: cr.Backend) -> None:
    _assert_encode_rejection(
        be,
        {"metrics": {"log": "line1\rline2"}},
        {
            "error": "UnrepresentableAt",
            "reason": "CRByte",
            "path": ["metrics", "log"],
            "spec_section": "§5.9.7",
        },
    )


@pytest.mark.parametrize("be", both())
def test_dotted_key_is_never_split_in_the_error_path(be: cr.Backend) -> None:
    _assert_encode_rejection(
        be,
        {"a.b": "x\ry"},
        {
            "error": "UnrepresentableAt",
            "reason": "CRByte",
            "path": ["a.b"],  # one segment — never split on the dot
            "spec_section": "§5.9.7",
        },
    )


@pytest.mark.parametrize("be", both())
def test_empty_key_name_rejection_carries_the_trailing_empty_segment(
    be: cr.Backend,
) -> None:
    # The key is pushed onto the path BEFORE the empty-key check, so the
    # path ends with the empty string itself (representable.rs: push then
    # `k.is_empty()`; writer.py 'pair' task: append then fail).
    _assert_encode_rejection(
        be,
        {"": "v"},
        {
            "error": "UnrepresentableAt",
            "reason": "EmptyKeyName",
            "path": [""],
            "spec_section": "§5.9.0",
        },
    )


@pytest.mark.parametrize("be", both())
def test_nested_non_finite_float_stays_pathless(be: cr.Backend) -> None:
    # The conversion guard (py_to_value / to_value) rejects NaN / ±Infinity
    # BEFORE any path-tracking pass, so the envelope stays honest `null`.
    _assert_encode_rejection(
        be,
        {"metrics": {"cpu": float("nan")}},
        {
            "error": "Unrepresentable",
            "reason": "NonFiniteFloat",
            "path": None,
            "spec_section": "§5.9.0",
        },
    )


# ---------------------------------------------------------------------------
# Focused pure-backend regressions (R3). These run in EVERY job (no
# native requirement); the dotted-path conflict path is the pure
# backend's decoded-path contract (parser.py insert_value: the whole
# raw path text is decoded, not just the prefix before the blocker).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("leaf_line", "leaf_desc"),
    [
        pytest.param("a: null", "null", id="null"),
        pytest.param("a: false", "false", id="false"),
        pytest.param("a: 0", "0", id="zero"),
        pytest.param("a:", '""', id="empty-string"),
    ],
)
def test_leaf_then_dotted_child_conflicts_with_the_full_decoded_path(
    leaf_line: str, leaf_desc: str
) -> None:
    """`a: <leaf>` then `a.b: 1` must CONFLICT, never overwrite, and the
    envelope must carry the FULL decoded path ["a", "b"]."""
    with pytest.raises(pure.KtavDecodeError) as exc_info:
        pure.loads(f"{leaf_line}\na.b: 1\n")
    assert exc_info.value.error == "KeyPathConflict"
    assert exc_info.value.path == ["a", "b"], f"leaf {leaf_desc}: full path required"


def test_dotted_child_then_leaf_conflicts() -> None:
    """`a.b: 1` then `a: x` — a leaf value cannot overwrite an object."""
    with pytest.raises(pure.KtavDecodeError) as exc_info:
        pure.loads("a.b: 1\na: x\n")
    assert exc_info.value.error == "KeyPathConflict"


def test_shared_acyclic_references_are_written_and_cycles_are_refused() -> None:
    """The same list object under two keys is ordinary shared structure
    (both spellings are the same empty array); only a value that lies on
    its own containment path is cyclic."""
    shared: list[Any] = []
    value = {"a": shared, "b": shared}
    # Hand-written canonical text for {"a": [], "b": []} (§ 5.9.3/5.9.4).
    assert pure.dumps(value) == "a: []\nb: []\n"
    assert pure.emit_canonical(value) == "a: []\nb: []\n"

    cyc: list[Any] = []
    cyc.append(cyc)
    with pytest.raises(pure.KtavEncodeError) as exc_info:
        pure.dumps({"a": cyc})
    assert exc_info.value.error == "Message"
    assert "cyclic" in str(exc_info.value)


def test_deep_multiline_nesting_400_round_trips_through_canonical() -> None:
    """400-deep MULTILINE compounds parse (iterative frame stack — no
    recursion on input depth) and emit_canonical reproduces the
    hand-computed canonical text exactly."""
    depth = 400
    source = "".join(f"k{d}: {{\n" for d in range(depth)) + "leaf: 1\n" + "}\n" * depth
    value = pure.loads(source)
    inner: Any = value
    for d in range(depth):
        assert isinstance(inner, dict), f"level {d} must be an object"
        assert list(inner) == [f"k{d}"], f"level {d} must hold exactly one key"
        inner = inner[f"k{d}"]
    # Hand-written innermost expectation.
    assert inner == {"leaf": 1}
    # Hand-computed canonical text: each level indents 4 more spaces.
    expected = (
        "".join(f"{'    ' * d}k{d}: {{\n" for d in range(depth))
        + f"{'    ' * depth}leaf: 1\n"
        + "".join(f"{'    ' * (depth - 1 - d)}}}\n" for d in range(depth))
    )
    assert pure.emit_canonical(value) == expected
    assert pure.loads(expected) == value


@pytest.mark.parametrize(
    ("depth", "ok"),
    [
        pytest.param(130, False, id="depth-130-rejected"),
        pytest.param(127, True, id="depth-127-parses"),
    ],
)
def test_inline_compound_accumulated_depth_boundary(depth: int, ok: bool) -> None:
    source = "[" * depth + "1" + "]" * depth
    if ok:
        value = pure.loads(source)
        inner: Any = value
        for _ in range(depth - 1):
            assert isinstance(inner, list), "each nesting level must be an array"
            assert len(inner) == 1, "each nesting level must hold exactly one item"
            inner = inner[0]
        assert inner == [1]
    else:
        with pytest.raises(pure.KtavDecodeError) as exc_info:
            pure.loads(source)
        assert exc_info.value.error == "MalformedInlineCompound"


def test_format_exact_public_text_per_dispatch_task_shape() -> None:
    """Each formatter dispatch task shape, pinned end-to-end through the
    public `format` with hand-written expected text."""
    # scalar pair ("value" task)
    assert pure.format("a: 1\n") == "a: 1\n"
    # comment + blank trivia ("trivia" task): comment verbatim, blank
    # runs collapse to one blank line
    assert pure.format("## c\n\na: 1\n") == "## c\n\na: 1\n"
    assert pure.format("## c\n\n\n\na: 1\n") == "## c\n\na: 1\n"
    # nested compound ("tobj" task): canonical multiline spelling
    assert pure.format("a: {b: {c: 1}}\n") == "a: {\n    b: {\n        c: 1\n    }\n}\n"
    # array items ("titem" task): one item per line
    assert pure.format("a: [1, 2]\n") == "a: [\n    1\n    2\n]\n"


def test_nested_inline_object_depth_boundary() -> None:
    """The nested inline-OBJECT path (whose accumulated-depth reset was
    repaired): `a: {b: {b: ... 1}}` — 130 nested inline compounds must
    be rejected with MalformedInlineCompound, 127 must parse with the
    exact hand-walked structure."""
    with pytest.raises(pure.KtavDecodeError) as exc_info:
        pure.loads("a: " + "{b: " * 130 + "1" + "}" * 130)
    assert exc_info.value.error == "MalformedInlineCompound"
    depth = 127
    value = pure.loads("a: " + "{b: " * depth + "1" + "}" * depth)
    # {"a": {"b": {"b": ... {"b": 1} ...}}} — depth nested objects, the
    # innermost holding {"b": 1}; descend iteratively, no recursion.
    inner: Any = value["a"]
    for _ in range(depth - 1):
        assert isinstance(inner, dict), "each level must be an object"
        assert list(inner) == ["b"], "each level must hold exactly one key `b`"
        inner = inner["b"]
    assert inner == {"b": 1}


def test_two_thousand_segment_dotted_key_parses_iteratively() -> None:
    """A 2_001-segment dotted key must parse without RecursionError and
    build the exact nested structure — hand-computed: 2_000 synthetic
    objects (one per leading `a` segment) around the leaf {"z": 1},
    i.e. 2_001 dict levels from the root. Only structure is asserted —
    no emission of the (quadratically indented) canonical text."""
    segments = 2001
    value = pure.loads("a." * (segments - 1) + "z: 1")
    inner: Any = value
    for _ in range(segments - 1):
        assert isinstance(inner, dict), "each leading segment must open an object"
        assert list(inner) == ["a"], "each synthetic level must hold exactly one key `a`"
        inner = inner["a"]
    assert inner == {"z": 1}, "the final segment must hold the leaf value"


def test_multiline_object_depth_1200_beyond_default_recursion_limit() -> None:
    """1_200-deep EXPLICIT MULTILINE object nesting (beyond CPython's
    default 1_000 recursion limit) must parse iteratively. Canonical
    emission is asserted by STRUCTURAL FACTS only — total line count,
    first and last lines, and a reparse — never by materializing the
    whole ~2.4MB text in a single comparison, keeping CI cost bounded."""
    depth = 1200
    source = "".join(f"k{d}: {{\n" for d in range(depth)) + "leaf: 1\n" + "}\n" * depth
    value = pure.loads(source)
    inner: Any = value
    for d in range(depth):
        assert isinstance(inner, dict), f"level {d} must be an object"
        assert list(inner) == [f"k{d}"], f"level {d} must hold exactly one key"
        inner = inner[f"k{d}"]
    assert inner == {"leaf": 1}
    out = pure.emit_canonical(value)
    lines = out.splitlines()
    # depth open lines + 1 leaf line + depth close lines.
    assert len(lines) == 2 * depth + 1
    assert lines[0] == "k0: {"
    assert lines[depth] == "    " * depth + "leaf: 1"
    assert lines[-1] == "}"
    # A reparse of the canonical text equals the original value.
    assert pure.loads(out) == value

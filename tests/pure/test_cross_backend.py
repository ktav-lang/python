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


def test_inline_object_with_metadata_like_keys() -> None:
    """Keys named like the formatter's FORMER internal fields (`k`,
    `items`, `pairs`) are legal USER keys inside an inline object.

    # independent oracle — not derived from either backend
    PINS THE OLD BUG: the pre-sentinel formatter detected trivia nodes
    with string tags (`"k" in value`), so the legal key `k` made the
    whole inline object be misread as a trivia node and `pure.format`
    raised KeyError('items') (or silently mangled the value).

    Hand-written expectations: the parsed value, the multiline format
    text (one pair per line, 4-space indent per level, `key: value`),
    the fixed point, and the canonical text. The document has no
    comments or blank lines, so canonical == format here per the
    corpus rule."""
    doc = "a: {k: 1, items: [2], pairs: 3}\n"
    # independent oracle — not derived from either backend
    assert pure.loads(doc) == {"a": {"k": 1, "items": [2], "pairs": 3}}
    expected = "a: {\n    k: 1\n    items: [\n        2\n    ]\n    pairs: 3\n}\n"
    # independent oracle — not derived from either backend
    assert pure.format(doc) == expected
    assert pure.format(expected) == expected, "format must be a fixed point"
    # independent oracle — not derived from either backend
    assert pure.emit_canonical(pure.loads(doc)) == expected
    # Legal metadata keys nested one level deeper must not collide either.
    # independent oracle — not derived from either backend
    assert pure.loads("n: {k: {pairs: true}}") == {"n": {"k": {"pairs": True}}}


def test_dotted_reopen_of_inline_object_preserves_entries() -> None:
    """`a.y: 2` reopening the inline object from `a: {x: 1}` must KEEP
    the existing entry `x` (parsed value, format text, canonical text).

    # independent oracle — not derived from either backend
    PINS THE OLD BUG: trivia insertion replaced the untagged plain
    inline object with a FRESH EMPTY trivia node before adding `y`, so
    the formatter tree dropped `x` (formatter output lost `x: 1`).

    Hand-written expectations: value, field order, multiline format
    text, canonical text (== format here: no comments/blanks), and the
    fixed point. The doc is shallow, so plain `==` reparses fine."""
    doc = "a: {x: 1}\na.y: 2\n"
    value = pure.loads(doc)
    # independent oracle — not derived from either backend
    assert value == {"a": {"x": 1, "y": 2}}
    assert list(value["a"]) == ["x", "y"], "insertion order: x first, then reopened y"
    expected = "a: {\n    x: 1\n    y: 2\n}\n"
    # independent oracle — not derived from either backend
    assert pure.format(doc) == expected
    assert pure.format(expected) == expected, "format must be a fixed point"
    # independent oracle — not derived from either backend
    assert pure.emit_canonical(pure.loads(doc)) == expected
    # The formatted output reparses to the same value.
    assert pure.loads(expected) == value


def test_reopen_with_comment_preserves_comment_trivia() -> None:
    """`a.y: 2` reopening `a: {x: 1}` with a comment line before the
    reopen: the incoming `## keep` trivia must survive and be emitted
    immediately before the `y` pair at indent level 1.

    # independent oracle — not derived from either backend
    PINS THE PRE-REPAIR BUG: `_hook_pair` called `insert_value` BEFORE
    trivia insertion, so `y` was already in the plain object when
    `_adopt` converted it — the reopened leaf was adopted with EMPTY
    trivia and the incoming `## keep` comment was silently dropped from
    the formatted output — the format text lost the `## keep` line.
    The repaired decode-first flow: decode -> t_insert_decoded adopts
    the PRE-mutation `{"x": 1}` -> leaf `y` misses the adopted index ->
    appended WITH the incoming comment trivia -> plain insert adds `y`.

    Hand-written expectations: value, field order, exact format text,
    canonical text (comments are NOT data — § 5.9), fixed point, and
    reparse equality."""
    doc = "a: {x: 1}\n## keep\na.y: 2\n"
    value = pure.loads(doc)
    # independent oracle — not derived from either backend
    assert value == {"a": {"x": 1, "y": 2}}
    assert list(value["a"]) == ["x", "y"], "insertion order: x first, then reopened y"
    # The comment flushes immediately before the `y` pair at indent
    # level 1 (4 spaces).
    expected = "a: {\n    x: 1\n    ## keep\n    y: 2\n}\n"
    # independent oracle — not derived from either backend
    assert pure.format(doc) == expected
    assert pure.format(expected) == expected, "format must be a fixed point"
    # independent oracle — not derived from either backend
    # Canonical output carries NO comments (§ 5.9).
    assert pure.emit_canonical(pure.loads(doc)) == "a: {\n    x: 1\n    y: 2\n}\n"
    # Comments are not data: the formatted output reparses to the same
    # value.
    # independent oracle — not derived from either backend
    assert pure.loads(pure.format(doc)) == {"a": {"x": 1, "y": 2}}


def test_reopen_with_comment_and_metadata_like_names() -> None:
    """Reopen+comment regression using formatter-internal-looking field
    names (`obj`, `items`, `trailing`, `arr`, `pairs`, `k`): four
    reopened pairs under `obj.`, with one comment line before the FIRST
    reopened pair only.

    # independent oracle — not derived from either backend
    Hand-derivation of the format text against the parser's pending-
    trivia take semantics (parser.py `_hook_pending_key` /
    `_hook_pair`): each comment line accumulates into the parser's
    pending buffer; at the NEXT pair line `_hook_pending_key` TAKES the
    whole pending buffer into `key_trivia`, and `_hook_pair` attaches
    that trivia to the leaf only on the trivia-tree MISS branch. `## c`
    precedes `obj.items`, whose leaf `items` misses (freshly created in
    the adopted `obj` node) -> the comment attaches to `items` alone.
    `trailing`/`arr`/`pairs` then take EMPTY pending buffers, so no
    trivia rides on them. Hence the comment attaches before the FIRST
    reopened pair only, and all four reopened pairs are still present
    in order after `k`."""
    doc = "obj: {k: 1}\n## c\nobj.items: 2\nobj.trailing: 3\nobj.arr: 4\nobj.pairs: 5\n"
    value = pure.loads(doc)
    # independent oracle — not derived from either backend
    assert value == {"obj": {"k": 1, "items": 2, "trailing": 3, "arr": 4, "pairs": 5}}
    assert list(value["obj"]) == ["k", "items", "trailing", "arr", "pairs"]
    expected = (
        "obj: {\n    k: 1\n    ## c\n    items: 2\n    trailing: 3\n    arr: 4\n    pairs: 5\n}\n"
    )
    # independent oracle — not derived from either backend
    assert pure.format(doc) == expected
    assert pure.format(expected) == expected, "format must be a fixed point"
    # independent oracle — not derived from either backend
    # Canonical strips the comment (comments are not data — § 5.9).
    assert pure.emit_canonical(pure.loads(doc)) == (
        "obj: {\n    k: 1\n    items: 2\n    trailing: 3\n    arr: 4\n    pairs: 5\n}\n"
    )
    # independent oracle — not derived from either backend
    assert pure.loads(pure.format(doc)) == {
        "obj": {"k": 1, "items": 2, "trailing": 3, "arr": 4, "pairs": 5}
    }


@pytest.mark.parametrize("be", both())
@pytest.mark.parametrize(
    ("source", "expected_category"),
    [
        pytest.param("a: null\na.b: 2\n", "KeyPathConflict", id="null-blocker"),
        pytest.param("a: []\na.b: 2\n", "KeyPathConflict", id="array-blocker"),
        pytest.param(
            "a: 1\na.b..c: 2\n",
            "KeyPathConflict",
            id="first-segment-blocker-beats-later-empty",
        ),
        pytest.param("a: {}\na.b{c: 2\n", "InvalidKey", id="invalid-later-segment"),
    ],
)
def test_dotted_insertion_error_priority_is_interleaved(
    be: cr.Backend, source: str, expected_category: str
) -> None:
    """Per-segment validate-and-descend insertion: the FIRST failing
    segment wins, so a scalar/null/array blocker on an EARLIER segment
    yields `KeyPathConflict` even when a LATER segment is empty or
    invalid — and with a valid dict blocker-free prefix, a later
    INVALID segment still yields `InvalidKey` (validation of later
    segments happens because descent succeeds).

    # independent oracle — not derived from either backend
    Expectations derived from the RUST reference insert walk
    (rust/src/document/parser/build/insert.rs): per segment trim ->
    EmptyKey -> check_key -> decode; non-leaf descent into a
    non-dict value raises KeyPathConflict immediately, before later
    segments are validated.

    PINS THE PRE-REPAIR BUG: the pure backend decoded the whole key
    UP FRONT, so `a: 1\\na.b..c: 2` failed with EmptyKey (later empty
    segment) instead of KeyPathConflict (first-segment blocker).
    """
    with pytest.raises(be.api.KtavDecodeError) as exc_info:
        be.api.loads(source)
    assert exc_info.value.error == expected_category


def test_formatter_rejects_array_blocked_dotted_reopen() -> None:
    """`a: [\\n]\\na.b: 1` — a dotted reopen blocked by an ARRAY value —
    must be a public `KeyPathConflict` decode error, both in `pure.loads`
    and in `pure.format`.

    # independent oracle — not derived from either backend
    PINS THE OLD BUG: the formatter decoded pairs with a tagged-array
    internal representation and let a plain `KeyError` (tag lookup on a
    list value) escape instead of the public category.
    """
    doc = "a: [\n]\na.b: 1\n"
    with pytest.raises(pure.KtavDecodeError) as exc_info:
        pure.loads(doc)
    assert exc_info.value.error == "KeyPathConflict"
    with pytest.raises(pure.KtavDecodeError) as exc_info:
        pure.format(doc)
    assert exc_info.value.error == "KeyPathConflict"


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
    public `format` with hand-written expected text.

    Blank-line expectations are derived from the RUST REFERENCE, not
    from the implementation's current behavior:
    - rust/src/document/parser/fmt_parser/positioned.rs:71-79
      (`push_blank_trivia`): a blank is dropped when no trivia is
      pending AND the current frame is still at its start (blank
      padding after a compound opener / before the first content), and
      a blank immediately after another blank is dropped (a run of 2+
      collapses to exactly one; fmt_parser/mod.rs:28-35 documents the
      contract). Comments are never collapsed.
    - rust/src/document/parser/fmt_parser/doc.rs:186-191
      (`trim_trailing_blanks`) applied at EOF (positioned.rs:126) and
      at every close bracket: trailing blank padding is dropped.
    - rust/src/document/render/formatted.rs:60-80 (`emit_trivia` /
      `emit_object_pairs`): the whole pending run — blanks INCLUDED —
      flushes verbatim before the pair it is attached to, so a blank
      BETWEEN a comment and its pair SURVIVES attach-to-first-key.
    The pure TriviaParser mirrors this one-for-one (parser.py:804-814
    `_at_start`/`_push_blank`, parser.py:799-802 `_trim_blanks`).
    """
    # scalar pair ("value" task)
    assert pure.format("a: 1\n") == "a: 1\n"
    # comment + blank trivia ("trivia" task): comment verbatim, blank
    # runs collapse to one blank line (positioned.rs:71-79)
    assert pure.format("## c\n\na: 1\n") == "## c\n\na: 1\n"
    assert pure.format("## c\n\n\n\na: 1\n") == "## c\n\na: 1\n"
    # Blank between the comment and its pair: pending is non-empty, so
    # the blank survives and flushes before the pair (formatted.rs:75).
    assert pure.format("## c\n\n\nb: 2\n") == "## c\n\nb: 2\n"
    # Mid-document blank run between pairs: the frame is no longer at
    # its start, so ONE blank survives, the rest collapse.
    assert pure.format("a: 1\n\n\n\nb: 2\n") == "a: 1\n\nb: 2\n"
    assert pure.format("a: 1\n\nb: 2\n") == "a: 1\n\nb: 2\n"
    # Blank immediately INSIDE a compound opener: at-start padding is
    # dropped (positioned.rs:71-79)
    assert pure.format("a: {\n\nb: 1\n}\n") == "a: {\n    b: 1\n}\n"
    # Blank before a close bracket: trailing padding is trimmed
    # (doc.rs:186-191, applied on close).
    assert pure.format("a: {\nb: 1\n\n}\n") == "a: {\n    b: 1\n}\n"
    # nested compound ("tobj" task): canonical multiline spelling
    assert pure.format("a: {b: {c: 1}}\n") == "a: {\n    b: {\n        c: 1\n    }\n}\n"
    # array items ("titem" task): one item per line
    assert pure.format("a: [1, 2]\n") == "a: [\n    1\n    2\n]\n"


def _assert_equal_trees(a: Any, b: Any, path: list[Any]) -> None:
    """EXPLICIT ITERATIVE PAIRED STRUCTURE WALK — a drop-in replacement
    for recursive `==` on deep containers.

    An explicit stack of (kind, x, y, path_node) tasks; per pair: same
    container kind (dict/dict or list/list), same length, matching keys
    in order, children pushed; leaves compared with `is` for None/bool
    sentinels, exact `==` plus copysign for floats (so -0.0 != 0.0), and
    exact `==` with a type check for every other scalar. Assertion
    messages carry ONLY the current path — never a repr of a whole tree.

    PATH HANDLING: each task carries a PARENT-LINKED path NODE (`None`
    for the root, `(key_or_index, parent_node)` for every child), so
    pushing a child is a single O(1) tuple creation — O(1) memory per
    level and LINEAR total memory for the whole walk (one node per
    visited pair). No `[*p, k]` path copying. The readable path is
    materialized ONLY on failure, by walking the parent chain to the
    root and reversing it.

    Handles FINITE trees and is DAG-SAFE: shared acyclic subtrees (the
    same two objects referenced from two different places) are verified
    once and skipped silently on revisit. True cycles fail fast: an
    `active` set of (id(x), id(y)) container pairs on the CURRENT
    comparison path detects a back-edge (revisit while active) and
    `pytest.fail`s with a path-only message; a `finished` set holds
    fully compared pairs, so a legitimate repeated DAG pair is never
    mistaken for a cycle. Bounded memory (pairs, not paths); no
    recursive `==`, no whole-tree repr, no ever-growing path copies.

    Counterfactual: `cyc = []; cyc.append(cyc)` compared against itself
    hits (id(cyc), id(cyc)) in `active` while its child is still
    pending — it fails clearly instead of looping forever.
    """

    def _render(node: Any) -> str:
        # Materialize the parent-linked chain only on failure.
        segments: list[Any] = []
        while node is not None:
            segments.append(node[0])
            node = node[1]
        segments.reverse()
        return repr(segments)

    # Fold the caller-provided root path into a linked chain once.
    root_node: Any = None
    for seg in path:
        root_node = (seg, root_node)

    active: set[tuple[int, int]] = set()
    finished: set[tuple[int, int]] = set()
    stack: list[tuple[str, Any, Any, Any]] = [("node", a, b, root_node)]
    while stack:
        kind, x, y, p = stack.pop()
        if kind == "leave":
            # All children of this container pair were compared: move it
            # from the active path to the finished set (verified once).
            pair: tuple[int, int] = (id(x), id(y))
            active.discard(pair)
            finished.add(pair)
            continue
        pair = (id(x), id(y))
        if pair in finished:
            continue  # shared acyclic subtree — already verified, skip
        if pair in active:
            pytest.fail(f"cyclic structures differ-or-loop at {_render(p)}")
        active.add(pair)
        # Leave marker pushed BEFORE the children, so LIFO pops it AFTER
        # all of them: the pair stays on the active path for the whole
        # subtree, then is retired to `finished`.
        stack.append(("leave", x, y, p))
        if isinstance(x, dict) or isinstance(y, dict):
            assert isinstance(x, dict), f"kind mismatch at {_render(p)}"
            assert isinstance(y, dict), f"kind mismatch at {_render(p)}"
            assert len(x) == len(y), f"length differs at {_render(p)}"
            assert list(x) == list(y), f"key order/set differs at {_render(p)}"
            # Plain per-key appends keep the child tasks in dict order;
            # a list-comprehension extend here would flip LIFO visit
            # order and change which mismatch fires first.
            for k in x:
                stack.append(("node", x[k], y[k], (k, p)))  # noqa: PERF401
        elif isinstance(x, list) or isinstance(y, list):
            assert isinstance(x, list), f"kind mismatch at {_render(p)}"
            assert isinstance(y, list), f"kind mismatch at {_render(p)}"
            assert len(x) == len(y), f"length differs at {_render(p)}"
            for i, (cx, cy) in enumerate(zip(x, y)):
                stack.append(("node", cx, cy, (i, p)))
        elif x is None or y is None:
            assert x is None, f"value differs at {_render(p)}"
            assert y is None, f"value differs at {_render(p)}"
        elif isinstance(x, bool) or isinstance(y, bool):
            assert isinstance(x, bool), f"value differs at {_render(p)}"
            assert isinstance(y, bool), f"value differs at {_render(p)}"
            assert x is y, f"value differs at {_render(p)}"
        elif isinstance(x, float) or isinstance(y, float):
            assert isinstance(x, float), f"value differs at {_render(p)}"
            assert isinstance(y, float), f"value differs at {_render(p)}"
            assert x == y, f"value differs at {_render(p)}"
            assert math.copysign(1.0, x) == math.copysign(1.0, y), (
                f"float sign differs at {_render(p)}"
            )
        else:
            assert type(x) is type(y), f"value differs at {_render(p)}"
            assert x == y, f"value differs at {_render(p)}"


def test_tree_walk_helper_accepts_shared_dag() -> None:
    """The helper's DAG safety, exercised directly on small containers:
    the same shared dict referenced from two keys must PASS — the
    `finished` set skips the already-verified pair instead of treating
    the revisit as a cycle."""
    shared = {"s": 1}
    a: dict[str, Any] = {"x": shared, "y": shared}
    b: dict[str, Any] = {"x": {"s": 1}, "y": {"s": 1}}
    _assert_equal_trees(a, b, [])


def test_tree_walk_helper_fails_cycles() -> None:
    """The helper's cycle detection, exercised directly: a self-
    referencing list compared against itself must FAIL via `pytest.fail`
    with a message carrying ONLY the path (rendered from the parent-
    linked chain) — never a repr of the tree."""
    cyc: list[Any] = []
    cyc.append(cyc)
    with pytest.raises(pytest.fail.Exception) as exc_info:
        _assert_equal_trees(cyc, cyc, [])
    msg = str(exc_info.value)
    assert "cyclic" in msg
    assert "[0]" in msg, f"message must carry the cycle path: {msg!r}"
    assert "{" not in msg, f"message must not contain a tree repr: {msg!r}"


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
    # A reparse of the canonical text equals the original value —
    # compared by the ITERATIVE walk above: `pure.loads(out) == value`
    # would invoke CPython's RECURSIVE dict equality on 1_200-deep
    # dicts and could itself RecursionError.
    _assert_equal_trees(pure.loads(out), value, [])


def test_multiline_array_depth_1200_beyond_default_recursion_limit() -> None:
    """1_200-deep EXPLICIT MULTILINE ARRAY nesting (beyond CPython's
    default 1_000 recursion limit) must parse iteratively.

    Multiline array ITEMS carry no `-` prefix: inside an array frame
    every non-blank, non-`]` line is one item (parser.py:587-610
    `_array_item_line` — a bare `[` line classifies as open-arr and
    pushes a nested frame; § 5.4). The deep document is therefore
    `[\n` * depth + item + `]\n` * depth. Canonical emission is
    asserted by structural facts only, and the reparse equality uses
    the iterative walk — no full-text comparison and no recursive
    dict/list `==`.
    """
    depth = 1200
    source = "[\n" * depth + "1\n" + "]\n" * depth
    value = pure.loads(source)
    inner: Any = value
    for d in range(depth):
        assert isinstance(inner, list), f"level {d} must be an array"
        assert len(inner) == 1, f"level {d} must hold exactly one item"
        inner = inner[0]
    # Hand-counted: 1200 `[` openers around the scalar `1`, so descending
    # [0] exactly 1200 times consumes every array and reaches the
    # innermost SCALAR `1` — not a one-item list.
    # independent oracle — not derived from either backend
    assert inner == 1
    out = pure.emit_canonical(value)
    lines = out.splitlines()
    # depth open lines + 1 leaf line + depth close lines.
    assert len(lines) == 2 * depth + 1
    assert lines[0] == "["
    assert lines[depth] == "    " * depth + "1"
    assert lines[-1] == "]"
    _assert_equal_trees(pure.loads(out), value, [])

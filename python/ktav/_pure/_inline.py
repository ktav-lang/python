"""Inline compounds (spec § 5.8).

Quote-aware, escape-aware closer scanning, top-level comma splitting,
and value parsing.

The gate scan decides — in one left-to-right pass — between a closed
compound (§ 5.2 rules 6/7), no matching closer (rule 9 →
``UnterminatedInlineCompound``, also for an unterminated quoted key
segment and for a crossed closer at the body's own level), and a
``BadEscapeSequence`` encountered first (§ 6.13 precedence). A matching
closer that is not the body's last byte is ``MalformedInlineCompound``
(rule 8).

Nested compounds are scanned as independent spans (the Rust core's
"recorded bounds" semantics): a value-start opener whose own span does
not close is literal data, and commas/closers inside a successfully
scanned nested span are opaque to the enclosing body. The scan is also
scalar-aware (§ 5.8.5): a ``{``/``[`` that is not the first
non-whitespace byte of a value is literal, even when balanced.
"""

from __future__ import annotations

from typing import Any, Union

from ._keys import (
    _quoted_span_end,
    _scan_escape,
    check_key,
    decode_key_segment,
    find_unescaped_colon,
    process_escapes,
    split_key_path,
)
from ._text import is_inline_whitespace, trim_inline
from .errors import raise_decode

__all__ = ["MAX_INLINE_DEPTH", "ScanError", "parse_inline_value"]

MAX_INLINE_DEPTH = 128

Value = Union[None, bool, int, float, str, list[Any], dict[Any, Any]]

_QUOTES = "\"'`"


class ScanError(Exception):
    """A scan-level failure (bad escape / unterminated)."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind  # "bad-escape:<seq>" | "unterminated"


def _scan_body(
    s: str,
    start: int,
    close_c: str,
    object_body: bool,
    top: bool,
    commas: list[int] | None,
    depth: int,
) -> int | None:
    """Scan one inline compound body from ``start``.

    ``start`` sits just past the opener; the walk runs to the body's
    matching closer.

    Returns the closer's index, or ``None`` when no matching closer
    exists (EOF, crossed closer, or a dead nested span). Raises
    :class:`ScanError` on a bad escape sequence anywhere, at the
    top level only on an unterminated quoted key segment (§ 6.11 /
    § 6.16 precedence), and at every nesting level — dead nested
    spans included — on ``kind == "depth"`` when nesting exceeds
    ``MAX_INLINE_DEPTH``.
    """
    if depth >= MAX_INLINE_DEPTH:
        raise ScanError("depth")
    n = len(s)
    in_key = object_body
    seg_start = object_body
    value_start = not object_body
    raw = False
    j = start
    while j < n:
        c = s[j]
        if c == "\\":
            try:
                _, length = _scan_escape(s, j)
            except ValueError as exc:
                raise ScanError("bad-escape:" + str(exc.args[0])) from exc
            j += length
            continue
        if in_key and seg_start and c in _QUOTES:
            end = _quoted_span_end(s, j)
            if end is None:
                if top:
                    raise ScanError("unterminated")
                return None
            j = end + 1
            seg_start = False
            continue
        if raw:
            # <inline-raw-scalar>: terminated by the first unescaped
            # `,` / `}` / `]`; openers are literal data (§ 4).
            if c == ",":
                if commas is not None:
                    commas.append(j)
                value_start = False
                j += 1
                continue
            if c == "}" or c == "]":
                if c == close_c:
                    return j
                return None
            value_start = False
            j += 1
            continue
        if c == ",":
            if commas is not None:
                commas.append(j)
            in_key = object_body
            seg_start = object_body
            value_start = True
            j += 1
            continue
        if c == "}" or c == "]":
            if c == close_c:
                return j
            # Crossed closer inside this body: the compound never
            # closes (§ 6.11). A nested caller treats this as a dead
            # span; the top level reports it as unterminated.
            if top:
                raise ScanError("unterminated")
            return None
        if in_key:
            if is_inline_whitespace(c):
                # Whitespace stays inside the segment; a quote after it
                # still opens a quoted segment (§ 5.3.3 positional rule).
                j += 1
                continue
            if c == ":":
                if j + 1 < n and s[j + 1] == ":":
                    raw = True
                    in_key = False
                    value_start = False
                    j += 2
                    continue
                in_key = False
                value_start = True
                j += 1
                continue
            if c == ".":
                seg_start = True
                j += 1
                continue
            seg_start = False
            j += 1
            continue
        if (c == "{" or c == "[") and value_start:
            sub_close = "}" if c == "{" else "]"
            sub = _scan_body(s, j + 1, sub_close, c == "{", False, None, depth + 1)
            if sub is None:
                # Dead span: the opener is literal data (§ 5.8.5 — a
                # value-start opener without a matching closer is the
                # enclosing scan's problem, and the enclosing body's
                # own commas/closers still apply inside it).
                value_start = False
                j += 1
                continue
            value_start = False
            j = sub + 1
            continue
        if is_inline_whitespace(c):
            j += 1
            continue
        value_start = False
        j += 1
    return None


def _ctx_of(line: int, line_text: str, span: dict[Any, Any]) -> tuple[int, str, dict[Any, Any]]:
    return line, line_text, span


def _emit_scan_error(err: ScanError, line: int, line_text: str, span: dict[Any, Any]) -> None:
    text = err.kind
    if text.startswith("bad-escape:"):
        sequence = text[len("bad-escape:") :]
        raise_decode(
            "BadEscapeSequence",
            line,
            line_text,
            span,
            f"Syntax error: Line {line}: BadEscapeSequence: invalid escape sequence '{sequence}'",
            body=sequence,
        )
    if text == "depth":
        raise_decode(
            "MalformedInlineCompound",
            line,
            line_text,
            span,
            f"Syntax error: Line {line}: MalformedInlineCompound: nesting depth"
            " exceeds limit (128)",
            body="nesting depth exceeds limit (128)",
        )
    raise_decode(
        "UnterminatedInlineCompound",
        line,
        line_text,
        span,
        f"Syntax error: Line {line}: UnterminatedInlineCompound: inline"
        " compound not closed on the same line",
    )


def _run_gate(text: str, line: int, line_text: str, span: dict[Any, Any], depth: int) -> int:
    """Find the matching closer of the compound ``text`` (with outer.

    delimiters) or raise the § 6.11 / § 6.13 error.
    """
    if depth >= MAX_INLINE_DEPTH:
        raise_decode(
            "MalformedInlineCompound",
            line,
            line_text,
            span,
            f"Syntax error: Line {line}: MalformedInlineCompound: nesting depth"
            " exceeds limit (128)",
            body="nesting depth exceeds limit (128)",
        )
    open_c = text[0]
    close_c = "}" if open_c == "{" else "]"
    try:
        closer = _scan_body(text, 1, close_c, open_c == "{", True, None, depth)
    except ScanError as err:
        _emit_scan_error(err, line, line_text, span)
        raise AssertionError("unreachable") from err  # pragma: no cover
    if closer is None:
        _emit_scan_error(ScanError("unterminated"), line, line_text, span)
    assert closer is not None
    return closer


def _split(text: str, line: int, line_text: str, span: dict[Any, Any], depth: int) -> list[str]:
    """Split a compound body (with outer delimiters) on top-level.

    commas. The gate has already ruled out scan-level defects.
    """
    open_c = text[0]
    close_c = "}" if open_c == "{" else "]"
    commas: list[int] = []
    _scan_body(text, 1, close_c, open_c == "{", False, commas, depth)
    end = len(text) - 1  # exclude the body's own closer
    segments: list[str] = []
    prev = 1  # exclude the opener
    for pos in commas:
        segments.append(text[prev:pos])
        prev = pos + 1
    segments.append(text[prev:end])
    return segments


def _malformed(line: int, line_text: str, span: dict[Any, Any], detail: str) -> None:
    raise_decode(
        "MalformedInlineCompound",
        line,
        line_text,
        span,
        f"Syntax error: Line {line}: MalformedInlineCompound: {detail}",
        body=detail,
    )


def parse_inline_value(
    text: str,
    line: int,
    line_text: str,
    span: dict[Any, Any],
    depth: int,
    strict: bool,
) -> Value:
    """Parse a closed inline compound ``{ … }`` / ``[ … ]`` — the full.

    body including the outer delimiters.
    """
    closer = _run_gate(text, line, line_text, span, depth)
    if closer != len(text) - 1:
        _malformed(line, line_text, span, "content after closing delimiter")
    open_c = text[0]
    body = text[1:-1]
    if trim_inline(body) == "":
        return {} if open_c == "{" else []
    segments = _split(text, line, line_text, span, depth)
    if open_c == "{":
        return _build_object(segments, line, line_text, span, depth, strict)
    return _build_array(segments, line, line_text, span, depth, strict)


def _build_object(
    segments: list[str],
    line: int,
    line_text: str,
    span: dict[Any, Any],
    depth: int,
    strict: bool,
) -> dict[Any, Any]:
    from .parser import classify_inline_scalar, classify_value_start, insert_value

    result: dict[Any, Any] = {}
    last = len(segments) - 1
    for idx, segment in enumerate(segments):
        if trim_inline(segment) == "":
            if idx == last and idx > 0:
                continue  # single trailing comma
            _malformed(line, line_text, span, "empty inline pair")
        scan = find_unescaped_colon(segment)
        if scan is None:
            _malformed(line, line_text, span, "inline object pair is missing a separator")
        assert scan is not None
        key_raw = segment[:scan]
        rest = segment[scan + 1 :]
        raw_marker = rest.startswith(":")
        key_trimmed = trim_inline(key_raw)
        _check_inline_key(key_trimmed, line, line_text, span)
        value_out: Value
        if raw_marker:
            value_out, _ = process_escapes(trim_inline(rest[1:]), line, line_text, span)
        else:
            body = trim_inline(rest)
            if body[:1] in "{[":
                # Nested inline compound (dispatch decided once, from
                # the value's first non-whitespace byte, § 5.8.5).
                _kind, value_out = classify_value_start(
                    body, line, line_text, span, strict, depth + 1
                )
            else:
                value_out = classify_inline_scalar(body, line, line_text, span, strict)
        insert_value(result, key_trimmed, value_out, line, line_text, span)
    return result


def _check_inline_key(key_trimmed: str, line: int, line_text: str, span: dict[Any, Any]) -> None:
    validity = check_key(key_trimmed)
    if validity == "empty":
        raise_decode(
            "EmptyKey",
            line,
            line_text,
            span,
            f"Empty key at line {line}",
        )
    if validity == "invalid":
        raise_decode(
            "InvalidKey",
            line,
            line_text,
            span,
            f"Invalid key at line {line}: '{key_trimmed}'",
            path=split_key_path(key_trimmed),
        )
    # A malformed escape inside the key is reported here (§ 6.13).
    decode_key_segment(key_trimmed, line, line_text, span)


def _build_array(
    segments: list[str],
    line: int,
    line_text: str,
    span: dict[Any, Any],
    depth: int,
    strict: bool,
) -> list[Any]:
    items: list[Any] = []
    last = len(segments) - 1
    for idx, segment in enumerate(segments):
        if trim_inline(segment) == "":
            if idx == last and idx > 0:
                continue  # single trailing comma
            _malformed(line, line_text, span, "empty inline array item")
        items.append(_inline_item(segment, line, line_text, span, depth, strict))
    return items


def _inline_item(
    segment: str,
    line: int,
    line_text: str,
    span: dict[Any, Any],
    depth: int,
    strict: bool,
) -> Value:
    from .parser import classify_inline_scalar

    body = trim_inline(segment)
    if not body:
        _malformed(line, line_text, span, "empty inline array item")
    if body[0] in "{[":
        closer = _run_gate(body, line, line_text, span, depth + 1)
        rest = trim_inline(body[closer + 1 :])
        if rest:
            _malformed(line, line_text, span, "content after closing delimiter")
        return parse_inline_value(body[: closer + 1], line, line_text, span, depth + 1, strict)
    return classify_inline_scalar(body, line, line_text, span, strict)

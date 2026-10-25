"""Shared primitives for the source-edit engine.

Error helpers, textual-path parsing (UTF-8 byte-offset errors),
category-exact value equality, target lookup/removal, line/EOL context
helpers, Rust-compatible line iteration, and top-level inline segment
splitting. Pure code motion from the former single-file engine; no
behavioural change.
"""

from __future__ import annotations

import math
from typing import Any

from ._inline import _scan_body
from ._text import WS_CHARS, WS_INLINE_CHARS
from .errors import (
    KtavEditError,
    KtavInvalidPathError,
    KtavNotFoundError,
    KtavUnsupportedError,
)

__all__ = [
    "INDENT_UNIT",
    "WS_CHARS",
    "WS_INLINE_CHARS",
    "_INDENT_UNIT",
    "_inline_segments",
    "_line_detect_eol",
    "_line_indent",
    "_line_start",
    "_lookup_value",
    "_not_found",
    "_parse_index",
    "_physical_line",
    "_physical_line_span",
    "_rust_lines",
    "_same",
    "_take_target",
    "_unsupported",
    "parse_path",
]

_INDENT_UNIT = "    "
INDENT_UNIT = _INDENT_UNIT


# ---------------------------------------------------------------------------
# Edit errors (internal raising helpers)
# ---------------------------------------------------------------------------


def _not_found() -> KtavEditError:
    return KtavNotFoundError("edit path does not address an existing value", error="EditNotFound")


def _unsupported(reason: str) -> KtavEditError:
    return KtavUnsupportedError(
        f"no lossless source edit: {reason}",
        error="EditUnsupported",
        body=reason,
    )


# ---------------------------------------------------------------------------
# Textual path parsing (byte-offset errors)
# ---------------------------------------------------------------------------


def parse_path(path: str) -> list[str]:
    r"""Split ``key1.key2\.0`` on unescaped dots; ``\.``/``\\`` decode.

    Other escapes, a trailing lone backslash, an empty path, and empty
    segments raise :class:`KtavInvalidPathError` whose ``body`` is the
    decimal UTF-8 byte offset of the offending position.
    """
    if path == "":
        raise KtavInvalidPathError(
            "invalid edit path (bad escape or empty segment) at byte 0",
            error="EditInvalidPath",
            body="0",
        )
    segments: list[str] = []
    cur: list[str] | None = None
    seg_start = 0  # char offset
    byte = 0  # byte offset of the current char
    i = 0
    n = len(path)
    while i < n:
        c = path[i]
        if c == ".":
            if i == seg_start and cur is None:
                raise KtavInvalidPathError(
                    f"invalid edit path (bad escape or empty segment) at byte {byte}",
                    error="EditInvalidPath",
                    body=str(byte),
                )
            segments.append("".join(cur) if cur is not None else path[seg_start:i])
            cur = None
            seg_start = i + 1
            byte += 1
            i += 1
        elif c == "\\":
            if i + 1 < n and path[i + 1] in ".\\":
                if cur is None:
                    cur = [path[seg_start:i]]
                cur.append("." if path[i + 1] == "." else "\\")
                i += 2
                byte += 2
            else:
                raise KtavInvalidPathError(
                    f"invalid edit path (bad escape or empty segment) at byte {byte}",
                    error="EditInvalidPath",
                    body=str(byte),
                )
        else:
            # Once an escape switched the segment into accumulate mode,
            # every following plain char must be appended too (mirrors
            # the Rust `cur.push_str` in the default branch) — otherwise
            # `a\.b` would decode to "a." and lose the trailing text.
            if cur is not None:
                cur.append(c)
            i += 1
            byte += len(c.encode("utf-8"))
    if seg_start == n and cur is None:
        raise KtavInvalidPathError(
            f"invalid edit path (bad escape or empty segment) at byte {byte}",
            error="EditInvalidPath",
            body=str(byte),
        )
    segments.append("".join(cur) if cur is not None else path[seg_start:])
    return segments


def _parse_index(seg: str) -> int | None:
    """Zero-based ASCII-digits array index; leading zeros OK, signs not."""
    if not seg or not all("0" <= ch <= "9" for ch in seg):
        return None
    return int(seg)


# ---------------------------------------------------------------------------
# Value equality (bool/int/float/str category-exact, order-free objects)
# ---------------------------------------------------------------------------


def _same(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if isinstance(a, str) or isinstance(b, str):
        return isinstance(a, str) and isinstance(b, str) and a == b
    if isinstance(a, int) or isinstance(b, int):
        return isinstance(a, int) and isinstance(b, int) and a == b
    if isinstance(a, float) or isinstance(b, float):
        if not (isinstance(a, float) and isinstance(b, float)) or a != b:
            return False
        # Signed zero: -0.0 == 0.0 numerically, but the Rust core keeps
        # Float as canonical text, where the lexemes differ — so a zero
        # sign flip is a REAL edit, never a no-op. Non-zero floats skip
        # this branch entirely (one comparison, no allocations).
        if a == 0.0:
            return math.copysign(1.0, a) == math.copysign(1.0, b)
        return True
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_same(a[k], b[k]) for k in a)
    return False


def _lookup_value(v: Any, segments: list[str]) -> Any:
    cur = v
    for seg in segments:
        if isinstance(cur, dict):
            if seg not in cur:
                return None
            cur = cur[seg]
        elif isinstance(cur, list):
            idx = _parse_index(seg)
            if idx is None or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


def _take_target(v: Any, segments: list[str]) -> Any:
    last, parents = segments[-1], segments[:-1]
    cur = v
    for seg in parents:
        if isinstance(cur, dict):
            cur = cur[seg]
        elif isinstance(cur, list):
            cur = cur[_parse_index(seg) or 0]
        else:
            raise _not_found()
    if isinstance(cur, dict):
        if last not in cur:
            raise _not_found()
        old = cur[last]
        cur[last] = None
        return old
    if isinstance(cur, list):
        idx = _parse_index(last)
        if idx is None or idx >= len(cur):
            raise _not_found()
        old = cur[idx]
        cur[idx] = None
        return old
    raise _not_found()


# ---------------------------------------------------------------------------
# Line / EOL context helpers
# ---------------------------------------------------------------------------


def _line_indent(text: str, pos: int) -> str:
    start = _line_start(text, pos)
    end = start
    n = len(text)
    while end < n and text[end] in " \t":
        end += 1
    return text[start:end]


def _line_start(text: str, pos: int) -> int:
    idx = max(text.rfind("\n", 0, pos), text.rfind("\r", 0, pos))
    return idx + 1


def _detect_eol(text: str, pos: int) -> str:
    n = len(text)
    i = pos
    while i < n:
        c = text[i]
        if c == "\n":
            return "\n"
        if c == "\r":
            return "\r\n" if i + 1 < n and text[i + 1] == "\n" else "\r"
        i += 1
    before = text[:pos]
    k = max(before.rfind("\n"), before.rfind("\r"))
    if k >= 0:
        if before[k] == "\r":
            return "\r\n" if k + 1 < len(before) and before[k + 1] == "\n" else "\r"
        # A trailing LF belongs to a CRLF pair when a CR precedes it
        # (Rust: `i > 0 && bytes[i - 1] == b'\r'`).
        if k > 0 and before[k - 1] == "\r":
            return "\r\n"
    return "\n"


def _physical_line_span(text: str, pos: int) -> tuple[int, int, str]:
    start = _line_start(text, pos)
    idx_n = text.find("\n", pos)
    idx_r = text.find("\r", pos)
    ends = [i for i in (idx_n, idx_r) if i != -1]
    end = min(ends) if ends else len(text)
    return start, end, text[start:end]


def _physical_line(text: str, pos: int) -> str:
    return _physical_line_span(text, pos)[2]


# Kept under the historical name used across the engine modules.
_line_detect_eol = _detect_eol


def _rust_lines(s: str) -> list[str]:
    """Rust ``str::lines`` semantics.

    Split on LF, strip one trailing CR per line, and drop the final
    empty piece after a trailing LF.
    """
    if not s:
        return []
    lines = s.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [ln[:-1] if ln.endswith("\r") else ln for ln in lines]


def _is_compound(body: str) -> bool:
    return (body.startswith("{") and body.endswith("}")) or (
        body.startswith("[") and body.endswith("]")
    )


def _inline_segments(body: str) -> list[tuple[int, int]]:
    """Top-level comma segments of a closed inline compound as spans."""
    open_c = body[0]
    close_c = "}" if open_c == "{" else "]"
    commas: list[int] = []
    _scan_body(body, 1, close_c, open_c == "{", False, commas, 0)
    spans: list[tuple[int, int]] = []
    prev = 1
    for pos in commas:
        spans.append((prev, pos))
        prev = pos + 1
    spans.append((prev, len(body) - 1))
    return spans

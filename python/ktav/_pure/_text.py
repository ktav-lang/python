"""Shared text primitives for the fixed § 3.3 whitespace class.

Line splitting with byte offsets, UTF-8 validation, and escape
sequence helpers.

Whitespace is the closed 25-code-point list of spec § 3.3 — never a
host-language primitive (Python's ``str.isspace()`` additionally treats
``U+001C``-``U+001F`` as whitespace, which would silently diverge).
"""

from __future__ import annotations

from .errors import raise_decode

__all__ = [
    "WS_CHARS",
    "WS_INLINE_CHARS",
    "byte_len",
    "checked_utf8_len",
    "is_inline_whitespace",
    "is_ktav_whitespace",
    "line_text_at",
    "split_lines",
    "validate_utf8",
]

# The 25 § 3.3 code points (Unicode White_Space as of Unicode 6.3),
# spelled out as explicit escapes so no editor ever mangles them.
WS_CHARS = "".join(
    chr(cp)
    for cp in (
        0x09,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x20,
        0x85,
        0xA0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    )
)
WS_INLINE_CHARS = WS_CHARS.replace("\n", "").replace("\r", "")

_WS_SET = frozenset(WS_CHARS)
_WS_INLINE_SET = frozenset(WS_INLINE_CHARS)


def is_ktav_whitespace(ch: str) -> bool:
    """The full § 3.3 set (25 code points)."""
    return ch in _WS_SET


def is_inline_whitespace(ch: str) -> bool:
    """Line-bounded § 3.3 view: the full set minus LF and CR."""
    return ch in _WS_INLINE_SET


def trim(s: str) -> str:
    """``str.strip`` restricted to the § 3.3 set (all 25 code points)."""
    return s.strip(WS_CHARS)


def trim_inline(s: str) -> str:
    """``str.strip`` restricted to line-bounded § 3.3 whitespace."""
    return s.strip(WS_INLINE_CHARS)


def lstrip_inline(s: str) -> str:
    return s.lstrip(WS_INLINE_CHARS)


def rstrip_inline(s: str) -> str:
    return s.rstrip(WS_INLINE_CHARS)


def validate_utf8(data: bytes) -> str:
    """Decode ``data`` as UTF-8 or raise ``InvalidUtf8`` (§ 6.15).

    The check runs before any grammar processing; the span covers the
    first invalid byte sequence (nonempty) and the 1-based line number
    is computed over the raw bytes exactly as § 3.2 defines
    terminators.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        start = exc.start
        # Width of the offending sequence: walk forward to the next
        # lead byte or EOF so the span is nonempty over the bad bytes.
        end = start + 1
        n = len(data)
        while end < n and (data[end] & 0xC0) == 0x80 and end - start < 4:
            end += 1
        line = data.count(b"\n", 0, start) + 1
        for i in range(start):
            if data[i] == 0x0D and (i + 1 >= n or data[i + 1] != 0x0A):
                line += 1
        raise_decode(
            "InvalidUtf8",
            line,
            None,
            {"start": start, "end": end},
            (
                "InvalidUtf8: input is not valid UTF-8; first invalid byte"
                f" sequence at byte offset {start}"
            ),
        )


def checked_utf8_len(text: str) -> int:
    """UTF-8 byte length of ``text``, rejecting lone surrogates (§ 6.15).

    Escape sequences never leave lone surrogates in the ``str`` — they
    are decoded to real code points (or rejected as
    ``BadEscapeSequence``) — so a lone surrogate here can only come
    from the caller's input string, which is the ``str`` equivalent of
    undecodable bytes. Fail closed with the same structured
    ``InvalidUtf8`` envelope as :func:`validate_utf8` instead of a raw
    ``UnicodeEncodeError``.
    """
    try:
        return len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        start = exc.start
        prefix = text[:start]
        byte_start = len(prefix.encode("utf-8"))
        line = prefix.count("\n") + 1
        for i, ch in enumerate(prefix):
            if ch == "\r" and (i + 1 >= len(prefix) or prefix[i + 1] != "\n"):
                line += 1
        raise_decode(
            "InvalidUtf8",
            line,
            None,
            {"start": byte_start, "end": byte_start + 3},
            (
                "InvalidUtf8: input is not valid UTF-8; lone surrogate at"
                f" character offset {start} (byte offset {byte_start})"
            ),
        )


def split_lines(text: str) -> list[tuple[str, int]]:
    """Split ``text`` into ``(line_text, byte_start)`` per § 3.2.

    LF, lone CR, and CR LF are all terminators; the final line needs no
    terminator. ``byte_start`` is the UTF-8 byte offset of the line's
    first byte (the caller has already skipped one leading BOM).
    """
    lines: list[tuple[str, int]] = []
    byte_pos = 0
    i = 0
    n = len(text)
    start = 0
    while i < n:
        ch = text[i]
        if ch == "\n":
            lines.append((text[start:i], byte_pos))
            i += 1
            byte_pos += 1 + _line_bytes(text, start, i - 1)
            start = i
        elif ch == "\r":
            lines.append((text[start:i], byte_pos))
            step = 2 if i + 1 < n and text[i + 1] == "\n" else 1
            byte_pos += 1 + _line_bytes(text, start, i) + (1 if step == 2 else 0)
            i += step
            start = i
        else:
            i += 1
    if start < n or start == 0:
        lines.append((text[start:], byte_pos))
    return lines


def _line_bytes(text: str, start: int, end: int) -> int:
    """UTF-8 byte length of ``text[start:end]`` excluding the terminator.

    byte(s) at ``end`` (the terminator itself is accounted for by the
    caller).
    """
    return len(text[start:end].encode("utf-8"))


def byte_len(s: str) -> int:
    """UTF-8 byte length of ``s``."""
    return len(s.encode("utf-8"))


def byte_offset_of(line_text: str, col: int, line_start: int) -> int:
    """Byte offset of ``line_text[col]`` given the line's byte start."""
    if col <= 0:
        return line_start
    return line_start + byte_len(line_text[:col])


def line_text_at(source: str, pos: int) -> str | None:
    r"""Return the source line containing byte offset ``pos``.

        Rust envelope parity; one trailing ``
    `` is stripped.
    """
    if not source:
        return None
    lines = split_lines(source)
    result: str | None = None
    for text, start in lines:
        if start <= pos:
            result = text
        else:
            break
    if result is None:
        return None
    if result.endswith("\r"):
        result = result[:-1]
    return result

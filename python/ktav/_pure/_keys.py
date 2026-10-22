"""Key-context scanning (spec § 4 / § 5.3 / § 5.3.3).

Pair-separator scanning with quoted-segment opacity, dotted-path
splitting, segment validation, and escape decoding.

All scanning here operates on a single pre-split source line, so the
line-bounded whitespace view (§ 3.3 minus LF/CR) is the correct class
throughout.
"""

from __future__ import annotations

from typing import Any

from ._text import is_inline_whitespace
from .errors import raise_decode

__all__ = [
    "check_key",
    "decode_key_segment",
    "find_unescaped_colon",
    "is_pair_shape",
    "key_is_single_segment",
    "quoted_span_end",
    "scan_unescaped_colon",
    "split_key_path",
]

_ESCAPABLE = set("\\,}]{nr.:\"'`")


def _skip_segment_ws(s: str, i: int) -> int:
    n = len(s)
    while i < n and is_inline_whitespace(s[i]):
        i += 1
    return i


def _quoted_span_end(s: str, open_idx: int) -> int | None:
    """Index of the matching unescaped closer, or ``None``."""
    quote = s[open_idx]
    j = open_idx + 1
    n = len(s)
    while j < n:
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == quote:
            return j
        j += 1
    return None


quoted_span_end = _quoted_span_end


def _has_quote_bytes(s: str) -> bool:
    return '"' in s or "'" in s or "`" in s


class ColonScan:
    """Outcome of the pair-separator scan (spec § 4)."""

    __slots__ = ("index", "kind")

    def __init__(self, kind: str, index: int = -1) -> None:
        self.kind = kind  # "found" | "absent" | "unterminated"
        self.index = index


def _find_unescaped_colon_fast(s: str) -> int | None:
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c == ":":
            return i
        if c == "\\":
            i += 2
        else:
            i += 1
    return None


def _key_prefix_quote_opaque(s: str, frm: int, cand: int) -> tuple[str, int]:
    """Is the candidate colon at ``cand`` inside a quoted key segment?

    Returns ``("opaque", 0)`` when it is not, ``("open", resume)`` when
    a quoted span covers it (``resume`` is one past its closer), or
    ``("unterminated", 0)`` when a segment-start quote never closes.
    """
    if not _has_quote_bytes(s[frm:cand]):
        return "opaque", 0
    i = frm
    seg_start = frm == 0
    n = cand
    while i < n:
        if seg_start:
            i = _skip_segment_ws(s, i)
            if i < n and s[i] in "\"'`":
                end = _quoted_span_end(s, i)
                if end is None:
                    return "unterminated", 0
                if end > cand:
                    return "open", end + 1
                i = end + 1
                seg_start = False
                continue
            seg_start = False
        if i >= n:
            break
        c = s[i]
        if c == "\\":
            i += 2
        elif c == ".":
            seg_start = True
            i += 1
        else:
            i += 1
    return "opaque", 0


def scan_unescaped_colon(s: str) -> ColonScan:
    """The § 4 separator-scanning rule over one line."""
    frm = 0
    while True:
        rel = _find_unescaped_colon_fast(s[frm:])
        if rel is None:
            break
        cand = frm + rel
        state, resume = _key_prefix_quote_opaque(s, frm, cand)
        if state == "opaque":
            return ColonScan("found", cand)
        if state == "open":
            frm = resume
            continue
        return ColonScan("unterminated")
    if _has_quote_bytes(s):
        # Decide absent vs unterminated with the full walk.
        i = 0
        seg_start = True
        n = len(s)
        while i < n:
            if seg_start:
                i = _skip_segment_ws(s, i)
                if i < n and s[i] in "\"'`":
                    end = _quoted_span_end(s, i)
                    if end is None:
                        return ColonScan("unterminated")
                    i = end + 1
                    seg_start = False
                    continue
                seg_start = False
            if i >= n:
                break
            c = s[i]
            if c == "\\":
                i += 2
            elif c == ".":
                seg_start = True
                i += 1
            elif c == ":":
                return ColonScan("found", i)
            else:
                i += 1
    return ColonScan("absent")


def find_unescaped_colon(s: str) -> int | None:
    scan = scan_unescaped_colon(s)
    return scan.index if scan.kind == "found" else None


def split_key_path(s: str) -> list[str]:
    """Split at unescaped dots; quoted-segment content stays opaque."""
    out: list[str] = []
    if not _has_quote_bytes(s):
        start = 0
        i = 0
        n = len(s)
        while i < n:
            c = s[i]
            if c == "\\":
                i += 2
            elif c == ".":
                out.append(s[start:i])
                start = i + 1
                i += 1
            else:
                i += 1
        out.append(s[start:])
        return out
    start = 0
    i = 0
    seg_start = True
    n = len(s)
    while i < n:
        if seg_start:
            i = _skip_segment_ws(s, i)
            if i < n and s[i] in "\"'`":
                end = _quoted_span_end(s, i)
                if end is None:
                    break
                i = end + 1
                seg_start = False
                continue
            seg_start = False
        if i >= n:
            break
        c = s[i]
        if c == "\\":
            i += 2
        elif c == ".":
            out.append(s[start:i])
            start = i + 1
            i += 1
            seg_start = True
        else:
            i += 1
    out.append(s[start:])
    return out


def key_is_single_segment(s: str) -> bool:
    if not _has_quote_bytes(s):
        i = 0
        n = len(s)
        while i < n:
            c = s[i]
            if c == "\\":
                i += 2
            elif c == ".":
                return False
            else:
                i += 1
        return True
    i = 0
    seg_start = True
    n = len(s)
    while i < n:
        if seg_start:
            i = _skip_segment_ws(s, i)
            if i < n and s[i] in "\"'`":
                end = _quoted_span_end(s, i)
                if end is None:
                    return True
                i = end + 1
                seg_start = False
                continue
            seg_start = False
        if i >= n:
            break
        c = s[i]
        if c == "\\":
            i += 2
        elif c == ".":
            return False
        else:
            i += 1
    return True


def _is_forbidden_control_byte(c: str) -> bool:
    o = ord(c)
    return (o < 0x20 and c not in "\t\v\f") or o == 0x7F


def _escaped_len(s: str, i: int) -> int:
    n = len(s)
    if i + 1 >= n:
        return 1
    if s[i + 1] != "u" or i + 6 > n:
        return 2
    hex4 = s[i + 2 : i + 6]
    if len(hex4) < 4 or any(ch not in "0123456789abcdefABCDEF" for ch in hex4):
        return 2
    value = int(hex4, 16)
    if not 0xD800 <= value <= 0xDBFF:
        return 6
    if i + 12 > n or s[i + 6] != "\\" or s[i + 7] != "u":
        return 6
    low_hex = s[i + 8 : i + 12]
    if len(low_hex) < 4 or any(ch not in "0123456789abcdefABCDEF" for ch in low_hex):
        return 6
    low = int(low_hex, 16)
    return 12 if 0xDC00 <= low <= 0xDFFF else 6


def _is_valid_bare_key(raw: str) -> bool:
    if not raw:
        return False
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == "\\":
            i += _escaped_len(raw, i)
            continue
        if c in ",{}[]()" or _is_forbidden_control_byte(c):
            return False
        i += 1
    return True


def check_key(raw: str) -> str:
    """Validate one outer-trimmed raw segment; ``"valid"``/``"empty"``.

    /``"invalid"`` (spec § 5.3.1).
    """
    if not raw:
        return "empty"
    first = raw[0]
    if first in "\"'`":
        end = _quoted_span_end(raw, 0)
        if end is None:
            return "invalid"
        if end != len(raw) - 1:
            return "invalid"
        i = 1
        while i < end:
            c = raw[i]
            if c == "\\":
                i += _escaped_len(raw, i)
                continue
            if _is_forbidden_control_byte(c):
                return "invalid"
            i += 1
        return "empty" if end == 1 else "valid"
    return "valid" if _is_valid_bare_key(raw) else "invalid"


def _scan_escape(s: str, i: int) -> tuple[str, int]:
    r"""Scan one escape at ``s[i] == '\\'``.

    Returns ``(decoded, length)``; raises ``ValueError`` with the
    offending sequence text.
    """
    n = len(s)
    if i + 1 >= n:
        raise ValueError("\\<end-of-line>")
    nxt = s[i + 1]
    simple = {
        "\\": "\\",
        ",": ",",
        "}": "}",
        "]": "]",
        "{": "{",
        "[": "[",
        "n": "\n",
        "r": "\r",
        ".": ".",
        ":": ":",
        '"': '"',
        "'": "'",
        "`": "`",
    }.get(nxt)
    if simple is not None:
        return simple, 2
    if nxt == "u":
        if i + 6 > n:
            raise ValueError(_malformed_unicode(s, i))
        hex4 = s[i + 2 : i + 6]
        if any(ch not in "0123456789abcdefABCDEF" for ch in hex4):
            raise ValueError(_malformed_unicode(s, i))
        value = int(hex4, 16)
        if 0xD800 <= value <= 0xDBFF:
            if (
                i + 12 <= n
                and s[i + 6] == "\\"
                and s[i + 7] == "u"
                and all(ch in "0123456789abcdefABCDEF" for ch in s[i + 8 : i + 12])
            ):
                low = int(s[i + 8 : i + 12], 16)
                if 0xDC00 <= low <= 0xDFFF:
                    combined = 0x10000 + (value - 0xD800) * 0x400 + (low - 0xDC00)
                    return chr(combined), 12
            raise ValueError(_malformed_unicode(s, i))
        if 0xDC00 <= value <= 0xDFFF:
            raise ValueError(_malformed_unicode(s, i))
        return chr(value), 6
    o = ord(nxt)
    if o < 0x80:
        raise ValueError("\\" + nxt)
    raise ValueError(f"\\<0x{o:02X}>")


def _malformed_unicode(s: str, i: int) -> str:
    end = min(i + 6, len(s))
    seq = "\\u"
    for ch in s[i + 2 : end]:
        o = ord(ch)
        if o < 0x80:
            seq += ch
        else:
            seq += f"<0x{o:02X}>"
    return seq


def process_escapes(text: str, line: int, line_text: str, span: dict[Any, Any]) -> tuple[str, bool]:
    """Decode § 3.7 escapes; returns ``(decoded, had_escape)``.

    ``line_text`` is the diagnostic source line for the envelope.
    """
    if "\\" not in text:
        return text, False
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "\\":
            try:
                ch, length = _scan_escape(text, i)
            except ValueError as seq:
                raise_decode(
                    "BadEscapeSequence",
                    line,
                    line_text,
                    span,
                    f"Syntax error: Line {line}: BadEscapeSequence: invalid"
                    f" escape sequence '{seq.args[0]}'",
                    body=str(seq.args[0]),
                )
            out.append(ch)
            i += length
        else:
            out.append(text[i])
            i += 1
    return "".join(out), True


def decode_key_segment(text: str, line: int, line_text: str, span: dict[Any, Any]) -> str:
    """Decode one validated raw segment (quoted or bare)."""
    if text and text[0] in "\"'`":
        interior = text[1:-1]
        return process_escapes(interior, line, line_text, span)[0]
    return process_escapes(text, line, line_text, span)[0]


def is_pair_shape(trimmed: str) -> bool:
    """The § 5.0.1 rule-6 phase-1 pair-candidate test (shape only)."""
    scan = scan_unescaped_colon(trimmed)
    if scan.kind != "found":
        return False
    idx = scan.index
    key_part = _rstrip_ws(trimmed[:idx])
    if not key_part:
        return False
    after = trimmed[idx + 1 :]
    if after.startswith(":"):
        return True
    return not after or is_inline_whitespace(after[0])


def _rstrip_ws(s: str) -> str:
    end = len(s)
    while end > 0 and is_inline_whitespace(s[end - 1]):
        end -= 1
    return s[:end]

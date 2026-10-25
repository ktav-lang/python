"""Replacement-body planning for the source-edit engine.

Scalar/String/compound body rendering, inline § 3.7 encoding, marker
(raw `::`) decision rules, verbatim block framing, pretty compound
rendering with reindentation, and the Block-slot replacement planner.
Pure code motion from the former single-file engine.
"""

from __future__ import annotations

from typing import Any

from ._edit_common import _INDENT_UNIT, _rust_lines, _unsupported
from ._inline import MAX_INLINE_DEPTH
from ._keys import is_pair_shape
from ._numbers import canonical_float
from ._text import is_ktav_whitespace
from .errors import KtavEditError
from .writer import (
    _item_needs_raw_marker,
    _needs_raw_marker,
    _Renderer,
    push_key_segment,
)

__all__ = [
    "_PlanCtx",
    "_block_replacement",
    "_encode_inline",
    "_inline_body",
    "_inline_compound_body",
    "_plan_string",
    "_plan_value",
    "_reindent",
    "_render_compound_body",
    "_scalar_body",
    "_verbatim_block_body",
]


def _scalar_body(v: Any) -> str:
    if v is None:
        return "null"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return canonical_float(v)
    raise _unsupported("internal: scalar_body called on a compound value")


def _push_inline_string(s: str, force_string: bool, out: list[str]) -> None:
    last = len(s) - 1
    for i, c in enumerate(s):
        if force_string and i == 0:
            out.append(f"\\u{ord(c):04X}")
        else:
            _encode_inline_char(out, c, i, last)


def _encode_inline_char(out: list[str], c: str, i: int, last: int) -> None:
    if c == "\\":
        out.append("\\\\")
    elif c == ",":
        out.append("\\,")
    elif c == "}":
        out.append("\\}")
    elif c == "]":
        out.append("\\]")
    elif c == "{":
        out.append("\\{")
    elif c == "[":
        out.append("\\[")
    elif c == "\n":
        out.append("\\n")
    elif c == "\r":
        out.append("\\r")
    elif (i == 0 or i == last) and is_ktav_whitespace(c):
        out.append(f"\\u{ord(c):04X}")
    else:
        out.append(c)


def _encode_inline(s: str, force_string: bool) -> str:
    out: list[str] = []
    _push_inline_string(s, force_string, out)
    return "".join(out)


def _push_inline_value(v: Any, depth: int, out: list[str]) -> None:
    if depth > MAX_INLINE_DEPTH:
        raise _unsupported("replacement nesting exceeds inline depth limit (128)")
    if isinstance(v, dict):
        out.append("{")
        for index, (key, value) in enumerate(v.items()):
            if index != 0:
                out.append(", ")
            parts: list[str] = []
            push_key_segment(key, False, parts)
            out.extend(parts)
            out.append(": ")
            if isinstance(value, str):
                _push_inline_string(value, _needs_raw_marker(value), out)
            else:
                _push_inline_value(value, depth + 1, out)
        out.append("}")
    elif isinstance(v, list):
        out.append("[")
        for index, value in enumerate(v):
            if index != 0:
                out.append(", ")
            if isinstance(value, str) and value == "":
                out.append("()")
            elif isinstance(value, str):
                _push_inline_string(value, _needs_raw_marker(value), out)
            else:
                _push_inline_value(value, depth + 1, out)
        out.append("]")
    elif isinstance(v, str):
        _push_inline_string(v, _needs_raw_marker(v), out)
    else:
        out.append(_scalar_body(v))


def _inline_compound_body(v: Any) -> str:
    out: list[str] = []
    _push_inline_value(v, 0, out)
    return "".join(out)


def _inline_body(replacement: Any, force_string: bool) -> str:
    if isinstance(replacement, str):
        return _encode_inline(replacement, force_string and _needs_raw_marker(replacement))
    if isinstance(replacement, (dict, list)):
        return _inline_compound_body(replacement)
    return _scalar_body(replacement)


class _PlanCtx:
    __slots__ = (
        "block_compound",
        "eol",
        "existing_raw",
        "indent",
        "inline_compound",
        "role_item_block",
        "root_first",
        "slot",
    )

    def __init__(
        self,
        slot: str,
        role_item_block: bool,
        existing_raw: bool,
        root_first: bool,
        indent: str,
        eol: str,
        inline_compound: bool,
        block_compound: bool,
    ) -> None:
        self.slot = slot  # "pair" | "item" | "block"
        self.role_item_block = role_item_block
        self.existing_raw = existing_raw
        self.root_first = root_first
        self.indent = indent
        self.eol = eol
        self.inline_compound = inline_compound
        self.block_compound = block_compound


def _verbatim_block_body(s: str, indent: str, eol: str) -> str:
    for line in _rust_lines(s):
        if line.strip(" \t") == "))":
            raise _unsupported(
                "multiline string contains a line equal to '))'; no lossless verbatim form exists"
            )
    out = ["((", eol]
    first = True
    for line in s.split("\n"):
        if not first:
            out.append(eol)
        first = False
        out.append(line)
    out.append(eol)
    out.append(indent)
    out.append("))")
    return "".join(out)


def _render_compound_body(v: Any) -> str:
    out: list[str] = []
    renderer = _Renderer(False, False, out)
    try:
        if isinstance(v, dict):
            if not v:
                return "{}\n"
            out.append("{\n")
            renderer.render_object_body(v, 1, False)
            out.append("}\n")
        elif isinstance(v, list):
            if not v:
                return "[]\n"
            out.append("[\n")
            for item in v:
                renderer.render_item(item, 1, False)
            out.append("]\n")
        else:
            raise _unsupported("internal: render_compound_body on a scalar")
    except KtavEditError:
        raise
    except Exception as exc:  # KtavEncodeError from the § 5.9.0 walk
        raise _unsupported(f"replacement is not representable: {exc}") from exc
    return "".join(out)


def _reindent(doc: str, indent: str, eol: str) -> str:
    out: list[str] = []
    in_verbatim = False
    for i, line in enumerate(_rust_lines(doc)):
        if line.startswith(_INDENT_UNIT):
            line = line[len(_INDENT_UNIT) :]
        verbatim_open = line.endswith("((")
        verbatim_close = line.strip(" \t") == "))" and line != ""
        if i > 0:
            out.append(eol)
            if not (in_verbatim or line == ""):
                out.append(indent)
        out.append(line)
        if verbatim_open:
            in_verbatim = True
        elif verbatim_close:
            in_verbatim = False
    return "".join(out)


def _plan_value(replacement: Any, pc: _PlanCtx) -> tuple[str, bool]:
    if isinstance(replacement, str):
        return _plan_string(replacement, pc)
    if replacement is None or isinstance(replacement, (bool, int, float)):
        return _scalar_body(replacement), False
    if pc.inline_compound:
        return _inline_compound_body(replacement), False
    if isinstance(replacement, dict) and not replacement:
        body = f"{{{pc.eol}{pc.indent}}}" if pc.block_compound else "{}"
        return body, False
    if isinstance(replacement, list) and not replacement:
        body = f"[{pc.eol}{pc.indent}]" if pc.block_compound else "[]"
        return body, False
    return _reindent(_render_compound_body(replacement), pc.indent, pc.eol), False


def _plan_string(s: str, pc: _PlanCtx) -> tuple[str, bool]:
    if "\r" in s:
        raise _unsupported("replacement string contains CR (U+000D)")
    edge_ws = bool(s) and (is_ktav_whitespace(s[0]) or is_ktav_whitespace(s[-1]))
    if "\n" in s or edge_ws:
        return _verbatim_block_body(s, pc.indent, pc.eol), False
    if pc.slot == "item":
        desired_raw = _item_needs_raw_marker(s) or s == ""
    else:
        desired_raw = _needs_raw_marker(s)
    if pc.slot == "item" and pc.root_first:
        desired_raw = desired_raw or is_pair_shape(s) or s.startswith("﻿")
    if pc.existing_raw:
        desired_raw = True
    return s, desired_raw


def _block_replacement(
    replacement: Any, pc: _PlanCtx, a: int, b0: int, ws_pair: str
) -> tuple[int, str, str]:
    """Returns (from, prefix, body)."""
    if isinstance(replacement, str):
        s = replacement
        if "\r" in s:
            raise _unsupported("replacement string contains CR (U+000D)")
        multiline = "\n" in s or (
            bool(s) and (is_ktav_whitespace(s[0]) or is_ktav_whitespace(s[-1]))
        )
        if multiline:
            return b0, "", _verbatim_block_body(s, pc.indent, pc.eol)
        if pc.role_item_block and s == "":
            return b0, "", "()"
        item_raw = pc.role_item_block and (
            _item_needs_raw_marker(s) or (pc.root_first and (is_pair_shape(s) or s.startswith("﻿")))
        )
        pair_raw = (not pc.role_item_block) and _needs_raw_marker(s)
        if item_raw:
            return b0, ":: ", s
        if pair_raw:
            return a + 1, ":" + ws_pair, s
        return b0, "", s
    pc2 = _PlanCtx(
        "block",
        pc.role_item_block,
        pc.existing_raw,
        pc.root_first,
        pc.indent,
        pc.eol,
        pc.inline_compound,
        pc.block_compound,
    )
    body, _ = _plan_value(replacement, pc2)
    return b0, "", body

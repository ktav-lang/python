"""Minimal inline unfolding for the source-edit engine.

Port of ``edit::splice::layout``: locate the physical inline wrapper
owning the splice, decide whether readability was lost (multiline
replacement, character-width growth beyond max(100, the previous line),
or dense escaping), and expand only the touched ancestor chain while
untouched nested branches stay inline. Pure code motion from the
former single-file engine.
"""

from __future__ import annotations

from typing import Any

from ._edit_common import (
    _INDENT_UNIT,
    _detect_eol,
    _inline_segments,
    _is_compound,
    _line_indent,
    _not_found,
    _parse_index,
    _physical_line,
    _physical_line_span,
    _rust_lines,
    _same,
    _unsupported,
)
from ._edit_encode import _encode_inline, _plan_value, _PlanCtx
from ._inline import MAX_INLINE_DEPTH, ScanError
from ._keys import find_unescaped_colon, process_escapes
from ._text import WS_CHARS, WS_INLINE_CHARS
from .errors import KtavDecodeError
from .parser import parse_document

__all__ = ["_layout_adjust", "_requires_block"]


def _layout_adjust(
    source: str,
    candidate: str,
    root: Any,
    path: list[str],
    replacement: Any,
    splice: tuple[int, int, int],
    *,
    trim_owner_trailing: bool = False,
) -> str:
    frm, to, inserted = splice
    owner = _inline_owner(source, root, path, frm, trim_owner_trailing)
    if owner is None:
        return candidate
    start, end = owner
    if frm < start:
        return candidate
    new_end = end - (to - frm) + inserted
    if not (0 <= start <= new_end <= len(candidate)):
        raise _unsupported("invalid layout boundaries")
    body = candidate[start:new_end]
    if not _is_compound(body):
        return candidate
    old_width = len(_physical_line(source, frm))
    limit = max(old_width, 100)
    force = _requires_block(replacement, 0)
    if not force and len(_physical_line(candidate, frm)) <= limit:
        return candidate
    indent = _line_indent(source, start)
    eol = _detect_eol(source, end)
    expanded = _expand(body, indent, eol, limit, (frm - start, frm - start + inserted), force, 0)
    if expanded is None:
        return candidate
    return candidate[:start] + expanded + candidate[new_end:]


def _slot_body(slot: tuple[Any, ...]) -> tuple[int, int]:
    if slot[0] == "block":
        return slot[2], slot[3]
    return slot[2], slot[3]


def _inline_owner(
    source: str,
    root: Any,
    path: list[str],
    pos: int,
    trim_trailing: bool = False,
) -> tuple[int, int] | None:
    node = root
    if root.inline:
        line_start, _line_end, raw_line = _physical_line_span(source, pos)
        lead = len(raw_line) - len(raw_line.lstrip(WS_CHARS))
        stripped = raw_line[lead:].lstrip("﻿")
        if trim_trailing:
            stripped = stripped.rstrip(WS_CHARS)
        bom_end = lead + (len(raw_line) - lead - len(raw_line[lead:].lstrip("﻿")))
        if trim_trailing:
            start = bom_end + (len(raw_line[bom_end:]) - len(raw_line[bom_end:].lstrip(WS_CHARS)))
            end = len(raw_line.rstrip(WS_CHARS))
            return line_start + start, line_start + end
        start = line_start + bom_end
        return start, start + len(stripped)
    for segment in path:
        if node.kind == "object":
            nxt = node.child(segment)
        elif node.kind == "array":
            idx = _parse_index(segment)
            if idx is None:
                raise _not_found()
            nxt = node.item(idx)
        else:
            nxt = None
        if nxt is None:
            raise _not_found()
        node = nxt
        if node.slot is not None:
            start, end = _slot_body(node.slot)
            if start <= len(source) and end <= len(source) and start <= end:
                body = source[start:end]
                if (
                    node.kind in ("object", "array")
                    and _is_compound(body)
                    and "\n" not in body
                    and "\r" not in body
                ):
                    return start, end
    if node.inline:
        line_start, _line_end, raw_line = _physical_line_span(source, pos)
        lead = len(raw_line) - len(raw_line.lstrip(WS_CHARS))
        trimmed_line = raw_line[lead:].lstrip("﻿")
        if trim_trailing:
            trimmed_line = trimmed_line.rstrip(WS_CHARS)
        base_shift = lead + (len(raw_line) - lead - len(raw_line[lead:].lstrip("﻿")))
        tail_body: str | None = None
        if _is_compound(trimmed_line):
            tail_body = trimmed_line
        else:
            colon = find_unescaped_colon(trimmed_line)
            if colon is not None:
                after_c = trimmed_line[colon + 1 :]
                tail_body = after_c.lstrip(WS_INLINE_CHARS)
                base_shift += colon + 1 + (len(after_c) - len(tail_body))
        if tail_body is not None and _is_compound(tail_body):
            base = line_start + base_shift
            return base, base + len(tail_body)
    return None


def _requires_block(value: Any, depth: int) -> bool:
    if depth > MAX_INLINE_DEPTH:
        raise _unsupported("replacement nesting exceeds inline depth limit (128)")
    if isinstance(value, str):
        if "\n" in value or "\r" in value:
            return True
        encoded = _encode_inline(value, False)
        escapes = 0
        i = 0
        while i < len(encoded):
            if encoded[i] == "\\":
                escapes += 1
                i += 2
                continue
            i += 1
        plain = len(value)
        overhead = max(0, len(encoded) - plain)
        return escapes >= 4 and overhead >= plain // 4 + (1 if plain % 4 else 0)
    if isinstance(value, dict):
        return any(_requires_block(c, depth + 1) for c in value.values())
    if isinstance(value, list):
        return any(_requires_block(c, depth + 1) for c in value)
    return False


def _expand(
    body: str,
    indent: str,
    eol: str,
    limit: int,
    changed: tuple[int, int],
    force: bool,
    depth: int,
) -> str | None:
    if depth > MAX_INLINE_DEPTH:
        raise _unsupported("layout nesting exceeds inline depth limit")
    is_object = body.startswith("{")
    try:
        spans = _inline_segments(body)
    except ScanError:
        raise _unsupported("cannot split inline layout") from None
    child_indent = indent + _INDENT_UNIT
    out: list[str] = ["{" if is_object else "["]
    for start, end in spans:
        seg = body[start:end]
        part = seg.strip(WS_INLINE_CHARS)
        if not part:
            continue
        offset = start + (len(seg) - len(seg.lstrip(WS_INLINE_CHARS)))
        touched = offset < changed[1] and offset + len(part) > changed[0]
        if is_object:
            colon = find_unescaped_colon(part)
            if colon is None:
                raise _unsupported("inline pair has no separator")
            after = part[colon + 1 :]
            raw = after.startswith(":")
            value = (after[1:] if raw else after).lstrip(WS_INLINE_CHARS)
            prefix = part[: len(part) - len(value)]
        else:
            prefix, value, raw = "", part, False
        out.append(eol)
        out.append(child_indent)
        if (
            not raw
            and _is_compound(value)
            and touched
            and (force or len(child_indent) + len(part) > limit)
        ):
            value_offset = offset + len(prefix)
            local = (
                max(0, changed[0] - value_offset),
                max(0, changed[1] - value_offset),
            )
            out.append(prefix)
            child = _expand(value, child_indent, eol, limit, local, force, depth + 1)
            if child is None:
                return None
            out.append(child)
        else:
            moved = _standalone(part, prefix, value, raw, is_object, child_indent, eol)
            if moved is None:
                return None
            out.append(moved)
    out.append(eol)
    out.append(indent)
    out.append("}" if is_object else "]")
    return "".join(out)


def _standalone(
    part: str,
    prefix: str,
    body: str,
    raw: bool,
    is_object: bool,
    indent: str,
    eol: str,
) -> str | None:
    inline = f"{{{part}}}" if is_object else f"[{part}]"
    try:
        expected = parse_document(inline)
    except KtavDecodeError:
        raise _unsupported("invalid inline layout") from None
    line = part if is_object else f"[\n{part}\n]"
    try:
        standalone_parses = parse_document(line)
    except KtavDecodeError:
        standalone_parses = None
    if standalone_parses is not None and _same(standalone_parses, expected):
        return part
    if raw:
        try:
            value: Any = process_escapes(body, 1, "", {"start": 0, "end": 0})[0]
        except KtavDecodeError:
            raise _unsupported("invalid inline string") from None
    else:
        wrapped = f"[{body}]"
        try:
            parsed = parse_document(wrapped)
        except KtavDecodeError:
            raise _unsupported("cannot decode moved inline value") from None
        if not (isinstance(parsed, list) and len(parsed) == 1):
            raise _unsupported("moved inline value is not a single value")
        value = parsed[0]
    if isinstance(value, str) and (
        "\r" in value or any(ln.strip(" \t") == "))" for ln in _rust_lines(value))
    ):
        return None
    pc = _PlanCtx(
        slot="pair" if is_object else "item",
        role_item_block=False,
        existing_raw=raw,
        root_first=False,
        indent=indent,
        eol=eol,
        inline_compound=True,
        block_compound=False,
    )
    new_body, desired_raw = _plan_value(value, pc)
    out: list[str] = []
    if is_object:
        colon = find_unescaped_colon(part)
        if colon is None:
            raise _unsupported("moved pair has no separator")
        out.append(part[: colon + 1])
        if desired_raw:
            out.append(":")
        ws = prefix[colon + 2 :] if raw else prefix[colon + 1 :]
        out.append(ws if ws else " ")
    elif desired_raw:
        out.append(":: ")
    out.append(new_body)
    return "".join(out)

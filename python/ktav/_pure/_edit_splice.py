"""Source-splice entry ops for the pure-Python edit engine.

Port of ``edit::splice::apply``: pre-parse the source (0.9 source-first
priority — the parser envelope wins over any edit-level error), look up
and compare the target, build the positional tree, plan the marker-zone
splice, apply the minimal layout adjustment, and re-parse + semantically
verify the result. Pure code motion from the former single-file engine.
"""

from __future__ import annotations

from typing import Any

from ._edit_common import (
    _detect_eol,
    _line_indent,
    _line_start,
    _lookup_value,
    _not_found,
    _parse_index,
    _same,
    _take_target,
    _unsupported,
)
from ._edit_encode import (
    _block_replacement,
    _inline_body,
    _plan_value,
    _PlanCtx,
)
from ._edit_layout import _layout_adjust
from ._edit_tree import (
    _build_tree,
    _collect_multiline_scalar_ranges,
    _descend,
    _has_comment_line,
    _Node,
)
from ._text import WS_CHARS
from .errors import KtavDecodeError
from .parser import parse_document

__all__ = [
    "apply_edit",
    "edit_value",
    "edit_value_segments",
    "insert_value",
    "insert_value_segments",
]


def _root_closer_line_start(text: str) -> int | None:
    end = len(text)
    while end > 0:
        start = _line_start(text, end - 1)
        stop = start
        while stop < len(text) and text[stop] not in "\r\n":
            stop += 1
        if text[start:stop].strip(WS_CHARS) == "}":
            return start
        end = start
    return None


def _sibling_indent(text: str, node: Any) -> str | None:
    children = node.children
    if node.kind != "object" or not isinstance(children, dict) or not children:
        return None
    last = next(reversed(children.values()))
    slot = last.slot
    if slot is None:
        return None
    pos = slot[1] if slot[0] in ("pair", "item") else slot[2]
    return _line_indent(text, _line_start(text, pos))


def _block_encodable(value: Any) -> bool:
    if isinstance(value, str):
        return "\r" not in value and not any(
            line.strip(" \t") == "))" for line in value.split("\n")
        )
    if isinstance(value, dict):
        return all(_block_encodable(child) for child in value.values())
    if isinstance(value, list):
        return all(_block_encodable(child) for child in value)
    return True


def _insert_pair(key: str, value: Any, indent: str, eol: str, inline: bool) -> str:
    """Render one newly inserted object member in block or inline form."""
    from ._edit_encode import _inline_body, _plan_value, _PlanCtx
    from .writer import push_key_segment

    parts: list[str] = []
    push_key_segment(key, False, parts)
    encoded_key = "".join(parts)
    if inline:
        return f"{encoded_key}: {_inline_body(value, True)}"
    pc = _PlanCtx("pair", False, False, False, indent, eol, False, True)
    body, raw = _plan_value(value, pc)
    return f"{encoded_key}:{':' if raw else ''} {body}"


def apply_edit(source: str, segments: list[str], replacement: Any) -> str:
    """Splice ``replacement`` over the value addressed by ``segments``.

    Source first: the source is validated and parsed BEFORE the path /
    replacement transport decode, so a malformed source surfaces as the
    real 0.9 parser envelope (line/line_text/span) — never as a
    coordinate-less :class:`KtavUnsupportedError`.
    """
    original = parse_document(source)
    target = _lookup_value(original, segments)
    if target is None and not _path_exists(original, segments):
        raise _not_found()
    if _same(target, replacement):
        return source
    root, root_explicit = _build_tree(source)
    node, inline, root_first = _descend(root, segments, root_explicit)
    slot = node.slot
    if slot is None:
        raise _unsupported(
            "target is a noncontiguous value (dotted-key/reopen intermediate); "
            "no lossless single-range splice exists"
        )

    slot_kind = slot[0]  # "pair" | "item" | "block"
    if slot_kind == "pair" or slot_kind == "item":
        body = (slot[2], slot[3])
        anchor = slot[1]
        block_item_role = False
    else:
        body = (slot[2], slot[3])
        anchor = slot[1] if slot[1] is not None else slot[2]
        block_item_role = slot[1] is None
    b0, b1 = body
    a = anchor

    if slot_kind == "block":
        existing_raw = False
        ws_raw = ""
        ws_plain = ""
    else:
        inline_item = inline and slot_kind == "item"
        if inline_item:
            existing_raw = False
            ws_raw = ""
            ws_plain = ""
        else:
            existing_raw = a + 1 < len(source) and source[a + 1] == ":"
            ws_raw = source[a + 2 : b0] if existing_raw else ""
            ws_plain = source[a + 1 : b0] if slot_kind == "pair" else ""

    if node.kind in ("object", "array"):
        ranges: list[tuple[int, int]] = []
        _collect_multiline_scalar_ranges(node, ranges)
        if _has_comment_line(source, b0, b1, ranges):
            raise _unsupported(
                "target container contains comment lines; structural "
                "replacement cannot preserve them losslessly"
            )

    indent = _line_indent(source, a)
    eol = _detect_eol(source, b1)
    pc = _PlanCtx(
        slot=slot_kind,
        role_item_block=slot_kind == "block" and block_item_role,
        existing_raw=existing_raw,
        root_first=root_first,
        indent=indent,
        eol=eol,
        inline_compound=slot_kind != "block" and node.kind in ("object", "array"),
        block_compound=slot_kind == "block" and node.kind in ("object", "array"),
    )
    ws_pair_block = "" if slot_kind != "block" or block_item_role else source[a + 1 : b0]

    if inline:
        if slot_kind == "item" and isinstance(replacement, str) and replacement == "":
            plan = (b0, "", "()")
        elif slot_kind == "item":
            plan = (b0, "", _inline_body(replacement, True))
        elif slot_kind == "pair" and existing_raw and not isinstance(replacement, str):
            plan = (a + 1, ws_raw, _inline_body(replacement, False))
        else:
            plan = (b0, "", _inline_body(replacement, not existing_raw))
    elif slot_kind == "block":
        plan = _block_replacement(replacement, pc, a, b0, ws_pair_block)
    else:
        new_body, desired_raw = _plan_value(replacement, pc)
        if existing_raw == desired_raw:
            prefix = " " if b0 == b1 and not ws_plain and not ws_raw else ""
            plan = (b0, prefix, new_body)
        elif existing_raw and not desired_raw and slot_kind == "pair":
            ws = ws_raw if b0 != b1 or ws_raw else " "
            plan = (a + 1, ws, new_body)
        elif existing_raw and not desired_raw:
            plan = (a, ws_raw, new_body)
        elif desired_raw and slot_kind == "pair":
            ws = ws_plain if b0 != b1 or ws_plain else " "
            plan = (a + 1, ":" + ws, new_body)
        else:
            plan = (a, ":: ", new_body)

    frm, prefix, new_body = plan
    result = source[:frm] + prefix + new_body + source[b1:]
    result = _layout_adjust(
        source, result, root, segments, replacement, (frm, b1, len(prefix) + len(new_body))
    )

    try:
        new_doc = parse_document(result)
    except KtavDecodeError as exc:
        raise _unsupported(f"patch produced an invalid document: {exc}") from None
    try:
        actual = _take_target(new_doc, segments)
        target_matches = _same(actual, replacement)
        expected = original
        _take_target(expected, segments)
    except (KeyError, IndexError, TypeError):
        # The patch re-parsed but no longer carries the target path — a
        # semantic mismatch, reported as the typed edit error, never as
        # an internal KeyError.
        raise _unsupported("semantic mismatch after splice; no lossless patch produced") from None
    if not target_matches or not _same(new_doc, expected):
        raise _unsupported("semantic mismatch after splice; no lossless patch produced")
    return result


def _path_exists(original: Any, segments: list[str]) -> bool:
    cur = original
    for seg in segments:
        if isinstance(cur, dict):
            if seg not in cur:
                return False
            cur = cur[seg]
        elif isinstance(cur, list):
            idx = _parse_index(seg)
            if idx is None or idx >= len(cur):
                return False
            cur = cur[idx]
        else:
            return False
    return True


def edit_value(source: str, path: str, replacement: Any) -> str:
    """Replace the value at the textual ``path`` in ``source``."""
    from ._edit_common import parse_path

    segments = parse_path(path)
    return _edit_segments_checked(source, segments, replacement)


def edit_value_segments(source: str, segments: list[str], replacement: Any) -> str:
    """Replace the value at already-decoded literal ``segments``."""
    if not segments:
        raise _not_found()
    return _edit_segments_checked(source, list(segments), replacement)


def _edit_segments_checked(source: str, segments: list[str], replacement: Any) -> str:
    from .writer import to_value

    value = to_value(replacement)
    return apply_edit(source, segments, value)


def insert_value(source: str, path: str, value: Any) -> str:
    """Insert a new Object member at textual ``path`` (parent.child)."""
    from ._edit_common import parse_path

    return insert_value_segments(source, parse_path(path), value)


def insert_value_segments(source: str, segments: list[str], value: Any) -> str:
    """Losslessly append a new member to an existing Object."""
    from ._edit_common import _detect_eol, _line_indent, _line_start, _parse_index
    from ._edit_layout import _requires_block
    from .errors import KtavAlreadyExistsError, KtavEditError
    from .writer import to_value

    original = parse_document(source)
    if not segments:
        raise _not_found()
    decoded = list(segments)
    if any(not isinstance(s, str) for s in decoded):
        raise KtavEditError("edit path segments must be strings", error="Message")
    value = to_value(value)
    replacement = value
    key, parents = decoded[-1], decoded[:-1]
    parent = _lookup_value(original, parents)
    if isinstance(parent, list):
        raise _unsupported(
            "insertion into an Array is not supported; only Object members can be created"
        )
    if not isinstance(parent, dict):
        raise _not_found()
    if key in parent:
        raise KtavAlreadyExistsError("object member already exists", error="EditAlreadyExists")
    root, root_explicit = _build_tree(source)
    node = root
    for seg in parents:
        child: _Node | None
        if node.kind == "object":
            child = node.child(seg)
        elif node.kind == "array":
            index = _parse_index(seg)
            child = node.item(index if index is not None else -1)
        else:
            child = None
        if child is None:
            raise _not_found()
        node = child
    eol = _detect_eol(source, len(source))
    slot = node.slot
    inline_body: tuple[int, int] | None = None
    if slot is not None and slot[0] in ("pair", "item"):
        b0, b1 = slot[2], slot[3]
        if b0 < b1 and source[b0] == "{" and source[b1 - 1] == "}":
            inline_body = (b0, b1)
    elif not parents and root.inline:
        from ._edit_common import _physical_line_span

        line_start = 0
        while line_start < len(source):
            _ls, _le, raw_line = _physical_line_span(source, line_start)
            line = raw_line.strip(WS_CHARS)
            if _ls == 0 and line.startswith("\ufeff"):
                line = line[1:]
            line = line.strip(WS_CHARS)
            if not line or line.startswith("#"):
                line_start = _le + (1 if _le < len(source) else 0)
                if (
                    _le < len(source)
                    and source[_le] == "\r"
                    and _le + 1 < len(source)
                    and source[_le + 1] == "\n"
                ):
                    line_start += 1
                continue
            leading = len(raw_line) - len(raw_line.lstrip(WS_CHARS))
            start = _ls + leading
            if _ls == 0:
                bom_end = start + len(raw_line[leading:]) - len(raw_line[leading:].lstrip("\ufeff"))
                start = bom_end
            start += len(raw_line[start - _ls :]) - len(raw_line[start - _ls :].lstrip(WS_CHARS))
            if line.startswith("{") and line.endswith("}"):
                inline_body = (start, start + len(line))
            break
    if inline_body is not None:
        a, b = inline_body
        eol = _detect_eol(source, b)
        inner = source[a + 1 : b - 1]
        indent = _line_indent(source, a)
        wants_block = _requires_block(replacement, 0) or (
            isinstance(replacement, str) and ("\n" in replacement or "\r" in replacement)
        )
        force = wants_block and _block_encodable(replacement)
        pair = _insert_pair(key, replacement, indent, eol, True)
        trimmed = inner.rstrip(WS_CHARS)
        if not inner.strip(WS_CHARS):
            at, to, inserted = a + 1, b - 1, pair
        else:
            comma = trimmed.endswith(",")
            slash_count = 0
            if comma:
                index = len(trimmed) - 2
                while index >= 0 and trimmed[index] == "\\":
                    slash_count += 1
                    index -= 1
            comma_is_structural = comma and slash_count % 2 == 0
            if comma_is_structural:
                at, to, inserted = a + 1 + len(trimmed), a + 1 + len(trimmed), " " + pair + ","
            else:
                at, to, inserted = b - 1, b - 1, ", " + pair
        result = source[:at] + inserted + source[to:]
        return _verify_insert_result(
            source, result, decoded, replacement, original, root, at, to, inserted, force
        )
    if not parents and root_explicit:
        closer = _root_closer_line_start(source)
        if closer is None:
            raise _unsupported("internal: explicit root without closer")
        sibling_indent = _sibling_indent(source, root)
        indent = "    " if sibling_indent is None else sibling_indent
        at = closer
        inserted = (
            indent
            + _insert_pair(key, replacement, indent, _detect_eol(source, at), False)
            + _detect_eol(source, at)
        )
        result = source[:at] + inserted + source[at:]
        return _verify_insert_result(
            source, result, decoded, replacement, original, root, at, at, inserted, False
        )
    if not parents:
        at = len(source)
        pair = _insert_pair(key, replacement, "", eol, False)
        lead = "" if not source or source.endswith(("\n", "\r")) else eol
        tail = eol if source and source.endswith(("\n", "\r")) else ""
        return _verify_insert_result(
            source,
            source + lead + pair + tail,
            decoded,
            replacement,
            original,
            root,
            at,
            at,
            lead + pair + tail,
            False,
        )
    if slot is None or slot[0] != "block":
        raise _unsupported("parent is a noncontiguous value; no lossless insertion point exists")
    end = slot[3]
    eol = _detect_eol(source, end)
    at = _line_start(source, end)
    sibling_indent = _sibling_indent(source, node)
    indent = _line_indent(source, slot[2]) + "    " if sibling_indent is None else sibling_indent
    pair_key = _insert_pair(key, replacement, indent, eol, False)
    inserted = indent + pair_key + eol
    result = source[:at] + inserted + source[at:]
    return _verify_insert_result(
        source, result, decoded, replacement, original, root, at, at, inserted, False
    )


def _clone_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clone_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_clone_value(child) for child in value]
    return value


def _verify_insert_result(
    source: str,
    result: str,
    segments: list[str],
    replacement: Any,
    original: Any,
    root: Any,
    frm: int,
    to: int,
    inserted: str,
    force: bool = False,
) -> str:
    from ._edit_common import _physical_line
    from ._edit_layout import _layout_adjust

    old_line = _physical_line(source, frm)
    new_line = _physical_line(result, frm)
    if (force or len(new_line) > max(len(old_line), 100)) and _block_encodable(replacement):
        result = _layout_adjust(
            source,
            result,
            root,
            segments[:-1],
            replacement,
            (frm, to, len(inserted)),
            trim_owner_trailing=True,
        )
    try:
        actual_doc = parse_document(result)
    except KtavDecodeError as exc:
        raise _unsupported(f"patch produced an invalid document: {exc}") from None
    try:
        expected = (
            dict(original)
            if not segments[:-1] and isinstance(original, dict)
            else _clone_value(original)
        )
        parent = expected
        for seg in segments[:-1]:
            if isinstance(parent, dict):
                parent = parent[seg]
            else:
                idx = _parse_index(seg)
                if idx is None:
                    raise KeyError(seg)
                parent = parent[idx]
        parent[segments[-1]] = replacement
    except (KeyError, IndexError, TypeError):
        raise _unsupported("semantic mismatch after splice; no lossless patch produced") from None
    if not _same(actual_doc, expected):
        raise _unsupported("semantic mismatch after splice; no lossless patch produced")
    return result

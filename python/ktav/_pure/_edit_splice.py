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
)
from .errors import KtavDecodeError
from .parser import parse_document

__all__ = ["apply_edit", "edit_value", "edit_value_segments"]


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

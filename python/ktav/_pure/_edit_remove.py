"""Pure-Python lossless positional removal edits."""
from __future__ import annotations

from typing import Any

from ._edit_common import (
    _lookup_value, _not_found, _parse_index, _same, _unsupported,
    _physical_line_span, _inline_segments,
)
from ._edit_tree import (
    _build_tree, _descend, _collect_multiline_scalar_ranges, _has_comment_line,
)
from .writer import push_key_segment
from ._inline import ScanError
from .errors import KtavDecodeError, KtavEditError
from .parser import parse_document
from ._text import WS_CHARS, WS_INLINE_CHARS

__all__ = ["remove_value_segments"]


def _clone(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clone(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_clone(child) for child in value]
    return value


def _line_end(source: str, pos: int) -> int:
    i = pos
    while i < len(source) and source[i] not in "\r\n":
        i += 1
    if i < len(source) and source[i] == "\r":
        i += 1
        if i < len(source) and source[i] == "\n":
            i += 1
    elif i < len(source):
        i += 1
    return i


def _line_start(source: str, pos: int) -> int:
    return max(source.rfind("\n", 0, pos), source.rfind("\r", 0, pos)) + 1


def _expected_without(original: Any, segments: list[str]) -> Any:
    expected = _clone(original)
    parent = expected
    for seg in segments[:-1]:
        if isinstance(parent, dict):
            if seg not in parent:
                raise _not_found()
            parent = parent[seg]
        elif isinstance(parent, list):
            idx = _parse_index(seg)
            if idx is None or idx >= len(parent):
                raise _not_found()
            parent = parent[idx]
        else:
            raise _not_found()
    key = segments[-1]
    if isinstance(parent, dict):
        if key not in parent:
            raise _not_found()
        del parent[key]
    elif isinstance(parent, list):
        idx = _parse_index(key)
        if idx is None or idx >= len(parent):
            raise _not_found()
        del parent[idx]
    else:
        raise _not_found()
    # Keep empty intermediate objects: no-prune semantics.
    return expected


def _inline_parent(source: str, root: Any, segments: list[str], explicit: bool, anchor: int) -> tuple[int, int]:
    parent, _inline, _first = _descend(root, segments[:-1], explicit)
    if parent.slot is not None:
        slot = parent.slot
        if slot[0] != "block":
            return slot[2], slot[3]
    if not segments[:-1] and root.inline:
        a, b, line = _physical_line_span(source, _line_start(source, anchor))
        lead = len(line) - len(line.lstrip(WS_CHARS))
        content = line[lead:]
        bom = 1 if content.startswith("\ufeff") else 0
        content = content[bom:]
        after_bom_lead = len(content) - len(content.lstrip(WS_CHARS))
        content = content[after_bom_lead:]
        content = content.rstrip(WS_CHARS)
        start = a + lead + bom + after_bom_lead
        return start, start + len(content)
    raise _unsupported("inline target without inline parent")


def _inline_range(source: str, root: Any, segments: list[str], explicit: bool, slot: tuple[Any, ...]) -> tuple[int, int]:
    anchor = slot[1]
    p0, p1 = _inline_parent(source, root, segments, explicit, anchor)
    body = source[p0:p1]
    if not body.endswith("}") and not body.endswith("]"):
        raise _unsupported("invalid inline parent range")
    try:
        spans = _inline_segments(body)
    except (ScanError, ValueError):
        raise _unsupported("cannot split inline parent for removal") from None
    parts: list[tuple[int, int]] = []
    for a, b in spans:
        raw = body[a:b]
        left = len(raw) - len(raw.lstrip(WS_INLINE_CHARS))
        right = len(raw.rstrip(WS_INLINE_CHARS))
        if left < right:
            parts.append((p0 + a + left, p0 + a + right))
    pos = next((i for i, (a, b) in enumerate(parts) if a <= anchor < b), None)
    if pos is None:
        raise _unsupported("target segment not found in inline parent")
    if len(parts) == 1:
        return p0 + 1, p1 - 1
    if pos + 1 < len(parts):
        return parts[pos][0], parts[pos + 1][0]
    return parts[pos - 1][1], parts[pos][1]


def _same_parse(candidate: str, expected: Any) -> bool:
    try:
        return _same(parse_document(candidate), expected)
    except KtavDecodeError:
        return False


def remove_value_segments(source: str, segments: list[str]) -> str:
    """Remove an existing value by decoded literal path segments."""
    original = parse_document(source)
    if not segments:
        raise _not_found()
    if any(not isinstance(segment, str) for segment in segments):
        raise KtavEditError("edit path segments must be strings", error="Message")
    expected = _expected_without(original, segments)
    root, explicit = _build_tree(source)
    node, _inline, _root_first = _descend(root, list(segments), explicit)
    slot = node.slot
    if slot is None:
        raise _unsupported("target is a noncontiguous value (dotted-key/reopen intermediate); no lossless single-range removal exists")
    if node.inline:
        start, end = _inline_range(source, root, list(segments), explicit, slot)
    else:
        anchor = slot[1] if slot[0] != "block" else slot[2]
        start = _line_start(source, anchor)
        if start == 0 and source.startswith("\ufeff"):
            start = 1
        end = _line_end(source, slot[3] if slot[0] != "block" else slot[3])
        if end == len(source) and not source[start:end].endswith(("\n", "\r")):
            if start and source[start - 1] == "\n":
                start -= 1
                if start and source[start - 1] == "\r":
                    start -= 1
            elif start and source[start - 1] == "\r":
                start -= 1
    if node.kind in ("object", "array"):
        ranges: list[tuple[int, int]] = []
        _collect_multiline_scalar_ranges(node, ranges)
        if _has_comment_line(source, start, end, ranges):
            raise _unsupported("target contains comment lines; removal cannot preserve them losslessly")

    cut_candidate = source[:start] + source[end:]
    if _same_parse(cut_candidate, expected):
        return cut_candidate

    replacement = None
    ancestors = segments[:-1]
    emptied_from = None
    for first in range(len(ancestors)):
        all_empty = True
        for depth in range(first, len(ancestors)):
            value = _lookup_value(expected, ancestors[:depth + 1])
            if not isinstance(value, dict) or value:
                all_empty = False
                break
        if all_empty:
            emptied_from = first
            break
    if emptied_from is not None:
        m = emptied_from
        synthetic, _inl, _first = _descend(root, ancestors[:m + 1], explicit)
        if synthetic.slot is None:
            container_depth = 0
            for depth in range(len(ancestors)):
                n, _, _ = _descend(root, ancestors[:depth + 1], explicit)
                if n.slot is not None:
                    container_depth = depth + 1
            if m >= container_depth:
                lead = 0
                if start < end and source[start:start + 2] == "\r\n":
                    lead = 2
                elif start < end and source[start:start + 1] in ("\r", "\n"):
                    lead = 1
                line_start = start + lead
                line_end = line_start
                while line_end < len(source) and source[line_end] in WS_CHARS:
                    line_end += 1
                indent = source[line_start:line_end]
                parts: list[str] = []
                for segment in ancestors[container_depth:]:
                    if parts:
                        parts.append(".")
                    push_key_segment(segment, False, parts)
                key = "".join(parts)
                replacement = source[start:line_start] + indent + key + ": {}"
                if end and source[end - 1] in "\r\n":
                    eol_start = end - 1
                    if source[eol_start] == "\n" and eol_start and source[eol_start - 1] == "\r":
                        eol_start -= 1
                    replacement += source[eol_start:end]

    candidate = source[:start] + (replacement or "") + source[end:]
    if _same_parse(candidate, expected):
        return candidate
    raise _unsupported("semantic mismatch after splice; no lossless patch produced")


"""Lossless source splice for renaming an existing Object key."""

from __future__ import annotations

from typing import Any

from ._edit_common import _lookup_value, _not_found, _parse_index, _same, _unsupported
from ._edit_tree import _build_tree, _descend
from ._keys import split_key_path
from ._text import is_inline_whitespace
from .errors import KtavAlreadyExistsError, KtavDecodeError, KtavEditError
from .parser import parse_document
from .writer import push_key_segment

__all__ = ["rename_key_segments"]


def _clone(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clone(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_clone(child) for child in value]
    return value


def rename_key_segments(source: str, segments: list[str], new_key: str) -> str:
    """Rename the final addressed Object member, preserving source layout."""
    original = parse_document(source)
    if not segments:
        raise _not_found()
    if not isinstance(new_key, str):
        raise KtavEditError("new key must be a string", error="Message")
    if not new_key:
        raise _unsupported("empty key name is not representable")
    key, parents = segments[-1], list(segments[:-1])
    parent = _lookup_value(original, parents)
    if isinstance(parent, list):
        raise _unsupported(
            "rename of an Array element is not supported; only Object keys can be renamed"
        )
    if not isinstance(parent, dict) or key not in parent:
        raise _not_found()
    if key == new_key:
        return source
    if new_key in parent:
        raise KtavAlreadyExistsError("object member already exists", error="EditAlreadyExists")

    root, root_explicit = _build_tree(source)
    parent_node, _inline, _root_first = _descend(root, parents, root_explicit)
    if parent_node.kind != "object":
        raise _unsupported("internal: parent node is not an object")
    target = parent_node.child(key)
    if target is None:
        raise _not_found()
    slot = target.slot
    if slot is None:
        raise _unsupported(
            "target is a noncontiguous value (dotted-key/reopen intermediate); "
            "no lossless rename range exists"
        )
    if slot[0] not in ("pair", "block") or (slot[0] == "block" and slot[1] is None):
        raise _unsupported(
            "rename of an Array element is not supported; only Object keys can be renamed"
        )
    colon = slot[1]
    # Find the final key segment within its pair, respecting inline
    # delimiters, quoted segments, escapes, dotted paths, and a leading BOM.
    key_end = colon
    while key_end > 0 and is_inline_whitespace(source[key_end - 1]):
        key_end -= 1
    start = max(source.rfind("\n", 0, colon), source.rfind("\r", 0, colon)) + 1
    if start == 0 and source.startswith("\ufeff"):
        start = 1
    boundary = start
    i = start
    segment_start = True
    while i < key_end:
        if segment_start:
            while i < key_end and is_inline_whitespace(source[i]):
                i += 1
            if i < key_end and source[i] in "\"'`":
                quote = source[i]
                i += 1
                while i < key_end:
                    if source[i] == "\\":
                        i += 2
                    elif source[i] == quote:
                        i += 1
                        break
                    else:
                        i += 1
                segment_start = False
                continue
            segment_start = False
        if source[i] == "\\":
            i += 2
            continue
        if source[i] == "." or source[i] in ",{[":
            boundary = i + 1
            segment_start = True
        i += 1
    while boundary < key_end and is_inline_whitespace(source[boundary]):
        boundary += 1
    start = boundary
    end = key_end
    raw_key = source[start:end]
    parts = split_key_path(raw_key)
    if not parts:
        raise _unsupported("internal: key without segments")
    last = parts[-1]
    seg_start = start + sum(len(part) + 1 for part in parts[:-1])
    first_root_key = not parents and next(iter(parent_node.children), None) == key
    encoded: list[str] = []
    push_key_segment(new_key, first_root_key, encoded)
    result = source[:seg_start] + "".join(encoded) + source[seg_start + len(last) :]

    expected = _clone(original)
    expect_parent = expected
    for segment in parents:
        if isinstance(expect_parent, list):
            index = _parse_index(segment)
            if index is None:
                raise _not_found()
            expect_parent = expect_parent[index]
        else:
            expect_parent = expect_parent[segment]
    renamed = {}
    for old, value in expect_parent.items():
        renamed[new_key if old == key else old] = value
    expect_parent.clear()
    expect_parent.update(renamed)
    try:
        actual = parse_document(result)
    except KtavDecodeError as exc:
        raise _unsupported(f"patch produced an invalid document: {exc}") from None
    if not _same(actual, expected):
        raise _unsupported("semantic mismatch after splice; no lossless patch produced")
    return result

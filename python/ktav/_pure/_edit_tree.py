"""Positional tree for the source-edit engine (port of ``edit::tree``).

One pass over the document's lines, mirroring the pure parser's line
dispatch decisions, but recording character-span slots (Pair / Item /
Block) instead of trivia. Dotted-key expansion and reopen follow the
parser's insertion semantics; reopen invalidates the slot of the
reopened node (noncontiguous). Inline compounds are positioned
recursively with the same child spans the parser scans.
"""

from __future__ import annotations

from typing import Any

from ._edit_common import (
    _inline_segments,
    _not_found,
    _parse_index,
    _unsupported,
)
from ._inline import MAX_INLINE_DEPTH
from ._keys import (
    check_key,
    decode_key_segment,
    find_unescaped_colon,
    split_key_path,
)
from ._text import WS_CHARS, WS_INLINE_CHARS, is_inline_whitespace

__all__ = [
    "_Node",
    "_build_tree",
    "_collect_multiline_scalar_ranges",
    "_descend",
    "_has_comment_line",
]


# ---------------------------------------------------------------------------
# Positional tree nodes
# ---------------------------------------------------------------------------


class _Node:
    __slots__ = ("children", "inline", "kind", "slot")

    def __init__(
        self, kind: str, children: Any, inline: bool, slot: tuple[Any, ...] | None
    ) -> None:
        self.kind = kind  # "scalar" | "object" | "array"
        self.children = children  # dict[str, Node] | list[Node] | None
        self.inline = inline
        # slot tuples:
        #   ("pair", colon, b0, b1)
        #   ("item", start, b0, b1)
        #   ("block", anchor|None, start, end)
        self.slot: tuple[Any, ...] | None = slot

    def child(self, key: str) -> _Node | None:
        if self.kind == "object" and isinstance(self.children, dict):
            return self.children.get(key)
        return None

    def item(self, i: int) -> _Node | None:
        if self.kind == "array" and isinstance(self.children, list):
            if 0 <= i < len(self.children):
                return self.children[i]
            return None
        return None


# ---------------------------------------------------------------------------
# Inline positioning (char spans over one physical line)
# ---------------------------------------------------------------------------


def _position_inline(
    body: str,
    base: int,
    line_num: int,
    line_text: str,
    span: dict[Any, Any],
    is_object: bool,
    depth: int,
) -> _Node:
    if depth > MAX_INLINE_DEPTH:
        raise _unsupported("replacement nesting exceeds inline depth limit (128)")
    spans = _inline_segments(body)
    if is_object:
        table: dict[str, _Node] = {}
        for start, end in spans:
            seg = body[start:end]
            trimmed = seg.strip(WS_INLINE_CHARS)
            if not trimmed:
                continue
            seg_base = base + start + (len(seg) - len(seg.lstrip(WS_INLINE_CHARS)))
            seg_end = seg_base + len(trimmed)
            colon = find_unescaped_colon(trimmed)
            if colon is None:
                raise _unsupported("internal: inline pair without separator")
            colon_abs = seg_base + colon
            key = trimmed[:colon]
            after = trimmed[colon + 1 :]
            if after.startswith(":"):
                # Raw `::`: body = second colon + whitespace run + value;
                # the raw body is literal String data, never a compound.
                rest = after[1:]
                v = rest.lstrip(WS_INLINE_CHARS)
                body_abs = seg_base + colon + 2 + (len(rest) - len(v))
                node = _Node("scalar", None, True, None)
            else:
                v = after.lstrip(WS_INLINE_CHARS)
                body_abs = seg_base + colon + 1 + (len(after) - len(v))
                node = _inline_child(v, body_abs, line_num, line_text, span, depth)
            node.slot = ("pair", colon_abs, body_abs, seg_end)
            _insert_leaf_value(table, key, node, line_num, line_text, span)
        return _Node("object", table, True, None)
    items: list[_Node] = []
    for start, end in spans:
        seg = body[start:end]
        trimmed = seg.strip(WS_INLINE_CHARS)
        if not trimmed:
            continue
        seg_base = base + start + (len(seg) - len(seg.lstrip(WS_INLINE_CHARS)))
        seg_end = seg_base + len(trimmed)
        value_abs = seg_base
        node = _inline_child(trimmed, value_abs, line_num, line_text, span, depth)
        node.slot = ("item", seg_base, value_abs, seg_end)
        items.append(node)
    return _Node("array", items, True, None)


def _inline_child(
    v: str, v_abs: int, line_num: int, line_text: str, span: dict[Any, Any], depth: int
) -> _Node:
    if v[:1] == "{":
        return _position_inline(v, v_abs, line_num, line_text, span, True, depth + 1)
    if v[:1] == "[":
        return _position_inline(v, v_abs, line_num, line_text, span, False, depth + 1)
    return _Node("scalar", None, True, None)


# ---------------------------------------------------------------------------
# Tree insertion with dotted-key / reopen semantics (parse already passed,
# so validation failures here are internal errors)
# ---------------------------------------------------------------------------


def _insert_leaf_value(
    table: dict[str, _Node],
    key_raw: str,
    value: _Node,
    line_num: int,
    line_text: str,
    span: dict[Any, Any],
) -> None:
    """Full dotted-key insertion; the LAST segment inserts ``value``."""
    segs = [s.strip(WS_INLINE_CHARS) for s in split_key_path(key_raw)]
    decoded: list[str] = []
    for seg in segs:
        validity = check_key(seg)
        if validity == "empty":
            raise _unsupported("internal: empty key segment while positioning")
        if validity == "invalid":
            raise _unsupported("internal: invalid key segment while positioning")
        decoded.append(decode_key_segment(seg, line_num, line_text, span))
    cur = table
    for key in decoded[:-1]:
        existing = cur.get(key)
        if existing is None:
            node = _Node("object", {}, False, None)
            cur[key] = node
            cur = node.children
        elif existing.kind == "object":
            existing.slot = None  # reopen: noncontiguous from here on
            cur = existing.children
        else:
            raise _unsupported("internal: dotted descent through a scalar")
    last = decoded[-1]
    if last in cur:
        raise _unsupported("internal: duplicate key while positioning")
    cur[last] = value


# ---------------------------------------------------------------------------
# Line shape classification (mirrors the Rust tree's classify_* helpers)
# ---------------------------------------------------------------------------


def _classify_value_shape(body: str) -> str:
    trimmed = body.strip(WS_INLINE_CHARS)
    if trimmed == "":
        return "empty-string"
    if trimmed == "{":
        return "open-obj"
    if trimmed == "[":
        return "open-arr"
    if trimmed.startswith("{"):
        if trimmed.endswith("}") and trimmed[1:-1].strip(WS_INLINE_CHARS) == "":
            return "empty-obj"
        return "inline"
    if trimmed.startswith("["):
        if trimmed.endswith("]") and trimmed[1:-1].strip(WS_INLINE_CHARS) == "":
            return "empty-arr"
        return "inline"
    if trimmed == "(":
        return "open-ml"
    if trimmed == "((":
        return "open-mlv"
    return "scalar"


def _classify_root_shape(trimmed: str) -> str:
    if trimmed.startswith("{"):
        return "inline-obj" if len(trimmed) > 1 else "explicit-obj"
    if trimmed.startswith("["):
        return "inline-arr" if len(trimmed) > 1 else "explicit-arr"
    if trimmed in ("}", "]"):
        return "bare-closer"
    scan = find_unescaped_colon(trimmed)
    if scan is not None:
        prefix = trimmed[:scan].rstrip(WS_INLINE_CHARS)
        after = trimmed[scan + 1 :]
        if prefix and (after.startswith(":") or after == "" or is_inline_whitespace(after[0])):
            return "obj"
    return "arr"


# ---------------------------------------------------------------------------
# Positional tree builder
# ---------------------------------------------------------------------------


def _split_lines_char(text: str) -> list[tuple[str, int]]:
    """(line_text, char_start) with LF / lone CR / CRLF terminators."""
    lines: list[tuple[str, int]] = []
    start = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            lines.append((text[start:i], start))
            i += 1
            start = i
        elif c == "\r":
            lines.append((text[start:i], start))
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            start = i
        else:
            i += 1
    lines.append((text[start:], start))
    return lines


class _Frame:
    __slots__ = ("anchor", "kind", "pending_key", "range_start", "table")

    def __init__(self, kind: str, range_start: int) -> None:
        self.kind = kind
        self.table: dict[str, _Node] | list[_Node] = {} if kind == "obj" else []
        self.pending_key: str | None = None
        self.anchor: int | None = None
        self.range_start = range_start


class _Collecting:
    __slots__ = ("anchor", "opener", "verbatim")

    def __init__(self, verbatim: bool, opener: int, anchor: int | None) -> None:
        self.verbatim = verbatim
        self.opener = opener
        self.anchor = anchor

    def terminator(self) -> str:
        return "))" if self.verbatim else ")"


def _build_tree(text: str) -> tuple[_Node, bool]:
    skip = 1 if text.startswith("\ufeff") else 0
    builder = _Builder()
    for line_num, (line_text, start) in enumerate(_split_lines_char(text[skip:]), start=1):
        builder.handle_line(line_text, start + skip, line_num)
    return builder.finish()


class _Builder:
    def __init__(self) -> None:
        self.stack: list[_Frame] = []
        self.collecting: _Collecting | None = None
        self.root_inline: _Node | None = None
        self.root_consumed = False
        self.root_is_explicit = False
        self.root_initialized = False

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _ts(line_text: str, line_start: int) -> tuple[int, int, str]:
        trimmed = line_text.strip(WS_CHARS)
        if not trimmed:
            return line_start, line_start + len(line_text), ""
        lead = len(line_text) - len(line_text.lstrip(WS_CHARS))
        start = line_start + lead
        return start, start + len(trimmed), trimmed

    @staticmethod
    def _line_ctx(line_num: int, line_text: str, start: int, end: int) -> dict[Any, Any]:
        return {"start": start, "end": end}

    def _last_frame(self) -> _Frame:
        return self.stack[-1]

    # -- dispatch ----------------------------------------------------------

    def handle_line(self, line_text: str, line_start: int, line_num: int) -> None:
        if self.collecting is not None:
            trimmed = line_text.strip(WS_CHARS)
            if trimmed == self.collecting.terminator():
                collecting = self.collecting
                self.collecting = None
                end = line_start + (len(line_text) - len(trimmed)) + len(trimmed)
                node = _Node(
                    "scalar", None, False, ("block", collecting.anchor, collecting.opener, end)
                )
                self._attach_scalar(node, line_num, line_start, line_text)
                return
            return

        start, end, trimmed = self._ts(line_text, line_start)
        span = self._line_ctx(line_num, line_text, start, end)
        if not trimmed or trimmed.startswith("##"):
            return
        if self.root_consumed:
            raise _unsupported("internal: orphan line after top-level inline")
        if not self.root_initialized:
            self.root_initialized = True
            if trimmed not in ("}", "]"):
                shape = _classify_root_shape(trimmed)
                if shape == "inline-obj":
                    self.root_consumed = True
                    self.root_inline = _position_inline(
                        trimmed, start, line_num, line_text, span, True, 0
                    )
                    return
                if shape == "inline-arr":
                    self.root_consumed = True
                    self.root_inline = _position_inline(
                        trimmed, start, line_num, line_text, span, False, 0
                    )
                    return
                if shape == "explicit-obj":
                    self.root_is_explicit = True
                    self.stack.append(_Frame("obj", start))
                    return
                if shape == "explicit-arr":
                    self.root_is_explicit = True
                    self.stack.append(_Frame("arr", start))
                    return
                if shape == "obj":
                    self.stack.append(_Frame("obj", 0))
                else:
                    self.stack.append(_Frame("arr", 0))

        if trimmed == "}":
            self._close_frame("obj", line_num, line_text, start, end)
            return
        if trimmed == "]":
            self._close_frame("arr", line_num, line_text, start, end)
            return

        if self._last_frame().kind == "arr":
            self._array_item(trimmed, line_num, line_text, start, end)
        else:
            self._object_pair(trimmed, line_num, line_text, start, end)

    # -- object pairs --------------------------------------------------------

    def _object_pair(
        self, line: str, line_num: int, line_text: str, ts_start: int, ts_end: int
    ) -> None:
        colon = find_unescaped_colon(line)
        if colon is None:
            raise _unsupported("internal: pair without separator")
        key = line[:colon].rstrip(WS_INLINE_CHARS)
        colon_off = ts_start + colon
        after = line[colon + 1 :]
        raw = after.startswith(":")
        rest = after[1:] if raw else after
        if rest and not is_inline_whitespace(rest[0]):
            raise _unsupported("internal: separator not followed by whitespace")
        value = rest.strip(WS_INLINE_CHARS)
        value_start = ts_start + colon + 1 + (len(after) - len(rest)) + (len(rest) - len(value))
        if raw:
            node = _Node("scalar", None, False, ("pair", colon_off, value_start, ts_end))
            self._insert_pair(key, node, line_num, line_text)
            return
        shape = _classify_value_shape(after)
        if shape in ("scalar", "empty-string"):
            node = _Node("scalar", None, False, ("pair", colon_off, value_start, ts_end))
            self._insert_pair(key, node, line_num, line_text)
        elif shape == "empty-obj":
            node = _Node("object", {}, False, ("pair", colon_off, value_start, ts_end))
            self._insert_pair(key, node, line_num, line_text)
        elif shape == "empty-arr":
            node = _Node("array", [], False, ("pair", colon_off, value_start, ts_end))
            self._insert_pair(key, node, line_num, line_text)
        elif shape in ("open-obj", "open-arr"):
            self._set_pending(key, colon_off)
            self.stack.append(_Frame("obj" if shape == "open-obj" else "arr", value_start))
        elif shape in ("open-ml", "open-mlv"):
            self._set_pending(key, colon_off)
            self.collecting = _Collecting(shape == "open-mlv", value_start, colon_off)
        else:  # inline
            node = _position_inline(
                value,
                value_start,
                line_num,
                line_text,
                {"start": ts_start, "end": ts_end},
                value.startswith("{"),
                0,
            )
            node.inline = False
            node.slot = ("pair", colon_off, value_start, ts_end)
            self._insert_pair(key, node, line_num, line_text)

    # -- array items ---------------------------------------------------------

    def _array_item(
        self, line: str, line_num: int, line_text: str, ts_start: int, ts_end: int
    ) -> None:
        if line.startswith("::"):
            rest = line[2:]
            if rest and not is_inline_whitespace(rest[0]):
                raise _unsupported("internal: raw marker without separator space")
            value = rest.lstrip(WS_INLINE_CHARS)
            body_start = ts_start + 2 + (len(rest) - len(value))
            node = _Node("scalar", None, False, ("item", ts_start, body_start, ts_end))
            self._push_item(node)
            return
        shape = _classify_value_shape(line)
        stripped = line.lstrip(WS_INLINE_CHARS)
        body_start = ts_start + (len(line) - len(stripped))
        if shape in ("scalar", "empty-string"):
            self._push_item(_Node("scalar", None, False, ("item", ts_start, body_start, ts_end)))
        elif shape == "empty-obj":
            self._push_item(_Node("object", {}, False, ("item", ts_start, body_start, ts_end)))
        elif shape == "empty-arr":
            self._push_item(_Node("array", [], False, ("item", ts_start, body_start, ts_end)))
        elif shape in ("open-obj", "open-arr"):
            self.stack.append(_Frame("obj" if shape == "open-obj" else "arr", body_start))
        elif shape in ("open-ml", "open-mlv"):
            self.collecting = _Collecting(shape == "open-mlv", body_start, None)
        else:  # inline
            node = _position_inline(
                stripped,
                body_start,
                line_num,
                line_text,
                {"start": ts_start, "end": ts_end},
                stripped.startswith("{"),
                0,
            )
            node.inline = False
            node.slot = ("item", ts_start, body_start, ts_end)
            self._push_item(node)

    # -- frames ----------------------------------------------------------------

    def _set_pending(self, key: str, anchor: int | None) -> None:
        frame = self._last_frame()
        if frame.kind != "obj":
            raise _unsupported("internal: pending key outside object frame")
        frame.pending_key = key
        frame.anchor = anchor

    def _insert_pair(self, key: str, node: _Node, line_num: int, line_text: str) -> None:
        frame = self._last_frame()
        if frame.kind != "obj" or not isinstance(frame.table, dict):
            raise _unsupported("internal: pair outside object frame")
        _insert_leaf_value(frame.table, key, node, line_num, line_text, {"start": 0, "end": 0})

    def _push_item(self, node: _Node) -> None:
        frame = self._last_frame()
        if frame.kind != "arr" or not isinstance(frame.table, list):
            raise _unsupported("internal: item outside array frame")
        frame.table.append(node)

    def _attach_scalar(self, node: _Node, line_num: int, line_start: int, line_text: str) -> None:
        frame = self._last_frame()
        if frame.kind == "obj" and isinstance(frame.table, dict):
            key = frame.pending_key
            if key is None:
                raise _unsupported("internal: multiline closed without pending key")
            frame.pending_key = None
            anchor = frame.anchor
            frame.anchor = None
            if node.slot is not None and node.slot[0] == "block":
                node.slot = ("block", anchor, node.slot[2], node.slot[3])
            _insert_leaf_value(frame.table, key, node, line_num, line_text, {"start": 0, "end": 0})
        elif isinstance(frame.table, list):
            frame.table.append(node)
        else:
            raise _unsupported("internal: multiline attach outside a frame")

    def _close_frame(
        self, expected: str, line_num: int, line_text: str, ts_start: int, ts_end: int
    ) -> None:
        if len(self.stack) == 1 and self.root_is_explicit:
            self.root_consumed = True
            return
        if len(self.stack) <= 1:
            raise _unsupported("internal: unbalanced bracket while positioning")
        frame = self.stack.pop()
        if frame.kind != expected:
            raise _unsupported("internal: mismatched bracket while positioning")
        anchor = None
        if self.stack and self.stack[-1].kind == "obj":
            anchor = self.stack[-1].anchor
            self.stack[-1].anchor = None
        node = _Node(
            "object" if frame.kind == "obj" else "array",
            frame.table,
            False,
            ("block", anchor, frame.range_start, ts_end),
        )
        parent = self._last_frame()
        if parent.kind == "obj" and isinstance(parent.table, dict):
            key = parent.pending_key
            if key is None:
                raise _unsupported("internal: closed compound without pending key")
            parent.pending_key = None
            _insert_leaf_value(parent.table, key, node, line_num, line_text, {"start": 0, "end": 0})
        elif isinstance(parent.table, list):
            parent.table.append(node)
        else:
            raise _unsupported("internal: close without a parent frame")

    # -- finish -------------------------------------------------------------------

    def finish(self) -> tuple[_Node, bool]:
        if self.collecting is not None or len(self.stack) > 1:
            raise _unsupported("internal: unclosed compound while positioning")
        if self.root_is_explicit and not self.root_consumed:
            raise _unsupported("internal: unclosed explicit root while positioning")
        if self.root_inline is not None:
            return self.root_inline, self.root_is_explicit
        if not self.stack:
            return _Node("object", {}, False, None), self.root_is_explicit
        frame = self.stack.pop()
        # Frame kinds are "obj"/"arr"; node kinds are "object"/"array".
        kind = "object" if frame.kind == "obj" else "array"
        return _Node(kind, frame.table, False, None), self.root_is_explicit


# ---------------------------------------------------------------------------
# Descent and comment scanning over the built tree
# ---------------------------------------------------------------------------


def _descend(root: _Node, segments: list[str], root_explicit: bool) -> tuple[_Node, bool, bool]:
    container_is_root = True
    cur = root
    root_first = False
    for seg in segments:
        if cur.kind == "object":
            root_first = False
            nxt = cur.child(seg)
            if nxt is None:
                raise _not_found()
            cur = nxt
        elif cur.kind == "array":
            idx = _parse_index(seg)
            if idx is None:
                raise _not_found()
            root_first = container_is_root and not root_explicit and idx == 0
            nxt = cur.item(idx)
            if nxt is None:
                raise _not_found()
            cur = nxt
        else:
            raise _not_found()
        container_is_root = False
    return cur, cur.inline, root_first


def _collect_multiline_scalar_ranges(node: _Node, out: list[tuple[int, int]]) -> None:
    if node.kind == "scalar" and node.slot is not None and node.slot[0] == "block":
        out.append((node.slot[2], node.slot[3]))
        return
    if node.kind == "object":
        for child in node.children.values():
            _collect_multiline_scalar_ranges(child, out)
    elif node.kind == "array":
        for child in node.children:
            _collect_multiline_scalar_ranges(child, out)


def _has_comment_line(text: str, frm: int, to: int, skip: list[tuple[int, int]]) -> bool:
    skip = sorted(skip)
    skip_i = 0
    i = frm
    while i < to:
        line_start = i
        j = line_start
        while j < to and text[j] not in "\n\r":
            j += 1
        line = text[line_start:j]
        trimmed = line.lstrip(WS_CHARS)
        k = line_start + (len(line) - len(trimmed))
        while skip_i < len(skip) and skip[skip_i][1] <= k:
            skip_i += 1
        in_data = skip_i < len(skip) and skip[skip_i][0] <= k < skip[skip_i][1]
        if not in_data and trimmed.startswith("##"):
            return True
        i = j
        while i < to and text[i] in "\n\r":
            i += 1
    return False

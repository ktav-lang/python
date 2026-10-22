"""The pure-Python Ktav parser (spec § 4 / § 5).

A single-pass, line-oriented scanner over UTF-8 text with UTF-8
byte-offset error spans, mirroring the Rust core's dispatch and
envelope.

Multi-line compounds are tracked with an explicit frame stack — no
recursion on input-controlled depth; inline compounds recurse only up
to the Rust core's declared 128-level bound. The :class:`TriviaParser`
subclass additionally preserves comment/blank-line trivia for the
``format`` backend.
"""

from __future__ import annotations

from typing import Any

from ._inline import Value, parse_inline_value
from ._keys import (
    check_key,
    decode_key_segment,
    key_is_single_segment,
    process_escapes,
    scan_unescaped_colon,
    split_key_path,
)
from ._numbers import (
    canonical_float,
    canonical_int,
    has_redundant_leading_zero,
    is_float_literal,
    parse_float_literal,
    parse_integer_literal,
)
from ._text import (
    WS_CHARS,
    WS_INLINE_CHARS,
    byte_len,
    checked_utf8_len,
    is_inline_whitespace,
    split_lines,
    trim,
    trim_inline,
)
from .errors import raise_decode

__all__ = [
    "PlainParser",
    "TriviaParser",
    "classify_scalar",
    "insert_value",
    "parse_document",
    "parse_with_trivia",
]

_WS_INLINE = WS_INLINE_CHARS

Trivia = list[tuple[bool, str]]  # (is_blank, text)

_MISSING = object()  # absent-key sentinel; null/false/0/"" are values


# ---------------------------------------------------------------------------
# Dotted-key insertion (§ 5.3.2 / § 6.3)
# ---------------------------------------------------------------------------


def insert_value(
    table: dict[Any, Any],
    path_text: str,
    value: Value,
    line: int,
    line_text: str,
    span: dict[Any, Any],
) -> None:
    """Insert ``value`` at the dotted ``path_text``.

    Mirrors the Rust outcome tables: per-segment validation
    (``EmptyKey`` / ``InvalidKey``), merge-and-reopen descent through
    existing objects, ``DuplicateKey`` on an occupied leaf, and
    ``KeyPathConflict`` when leaf/object shapes clash.
    """
    segments = [path_text] if key_is_single_segment(path_text) else split_key_path(path_text)
    node = table
    n = len(segments)
    decoded_path: list[str] = []  # accumulated decoded segments
    for idx, raw_seg in enumerate(segments):
        trimmed = trim_inline(raw_seg)
        if not trimmed:
            _empty_key(line, line_text, span)
        validity = check_key(trimmed)
        if validity == "empty":
            _empty_key(line, line_text, span)
        if validity == "invalid":
            raise_decode(
                "InvalidKey",
                line,
                line_text,
                span,
                f"Invalid key at line {line}: '{path_text}'",
                path=split_key_path(path_text),
            )
        decoded = decode_key_segment(trimmed, line, line_text, span)
        decoded_path.append(decoded)
        if idx + 1 == n:
            if decoded in node:
                existing = node[decoded]
                if isinstance(existing, dict) != isinstance(value, dict):
                    raise_decode(
                        "KeyPathConflict",
                        line,
                        line_text,
                        span,
                        (
                            "Syntax error: Line {}: conflict at '{}' — cannot overwrite {} with {}"
                        ).format(
                            line,
                            path_text,
                            "object" if isinstance(existing, dict) else "value",
                            "object" if isinstance(value, dict) else "value",
                        ),
                        path=list(decoded_path),
                    )
                raise_decode(
                    "DuplicateKey",
                    line,
                    line_text,
                    span,
                    f"Syntax error: Line {line}: duplicate key '{path_text}'",
                    path=list(decoded_path),
                )
            node[decoded] = value
            return
        existing = node.get(decoded, _MISSING)
        if existing is _MISSING:
            child: dict[Any, Any] = {}
            node[decoded] = child
            node = child
        elif isinstance(existing, dict):
            node = existing
        else:
            raise_decode(
                "KeyPathConflict",
                line,
                line_text,
                span,
                (
                    f"Syntax error: Line {line}: conflict at '{path_text}' - an existing"
                    " value blocks the path"
                ),
                path=list(decoded_path),
            )


def _empty_key(line: int, line_text: str, span: dict[Any, Any]) -> None:
    raise_decode("EmptyKey", line, line_text, span, f"Empty key at line {line}")


# ---------------------------------------------------------------------------
# § 5.2 scalar classification
# ---------------------------------------------------------------------------


def classify_scalar(
    body: str, line: int, line_text: str, span: dict[Any, Any], strict: bool
) -> Value:
    """§ 5.2 rules 10-15 for a trimmed, escape-processed scalar body."""
    if body == "null":
        return None
    if body == "true":
        return True
    if body == "false":
        return False
    if has_redundant_leading_zero(body):
        return body
    parsed_int = parse_integer_literal(body)
    if parsed_int is not None:
        canonical = canonical_int(parsed_int)
        if strict and canonical != body:
            _lossy(body, canonical, line, line_text, span)
        return parsed_int
    if is_float_literal(body):
        val = parse_float_literal(body)
        if val is not None:
            rendered = canonical_float(val)
            if strict and rendered != body:
                _lossy(body, rendered, line, line_text, span)
            return val
    return body


def _lossy(body: str, canonical: str, line: int, line_text: str, span: dict[Any, Any]) -> None:
    raise_decode(
        "LossyScalar",
        line,
        line_text,
        span,
        (
            f"Syntax error: Line {line}: LossyScalar: '{body}' would be inferred as a"
            f" number and silently canonicalised to '{canonical}'; append '::' to keep"
            " it a String or write the canonical form"
        ),
        body=body,
        canonical=canonical,
    )


def classify_inline_scalar(
    body: str, line: int, line_text: str, span: dict[Any, Any], strict: bool
) -> Value:
    """§ 5.8.5 inline scalar value: structural tokens first, then § 3.7.

    escape processing (any recognised escape forces String, § 5.2).
    """
    if body in ("()", "(())"):
        return ""
    decoded, had_escape = process_escapes(body, line, line_text, span)
    if had_escape:
        return decoded
    return classify_scalar(decoded, line, line_text, span, strict)


def classify_value_start(
    text: str, line: int, line_text: str, span: dict[Any, Any], strict: bool, depth: int = 0
) -> tuple[str, Any]:
    """§ 5.2 rules 1-15 for the value part of a line.

    ``depth`` is the enclosing inline nesting level; nested inline
    compounds accumulate toward the same 128-level bound. Returns
    ``(kind, payload)``: kind is ``"open-obj"``, ``"open-arr"``,
    ``"open-ml"``, ``"open-mlv"`` (payload ``None``), or ``"value"`` with
    the parsed value (inline compounds included).
    """
    trimmed = text.lstrip(_WS_INLINE)
    if trimmed == "{":
        return "open-obj", None
    if trimmed == "[":
        return "open-arr", None
    if trimmed.startswith(("{", "[")):
        if trimmed.endswith(("}", "]")) and trim_inline(trimmed[1:-1]) == "":
            return "value", ({} if trimmed[0] == "{" else [])
        return "value", _inline_gate(trimmed, line, line_text, span, depth, strict)
    if trimmed == "(":
        return "open-ml", None
    if trimmed == "((":
        return "open-mlv", None
    if trimmed in ("()", "(())"):
        return "value", ""
    return "value", classify_scalar(trimmed, line, line_text, span, strict)


def _inline_gate(
    trimmed: str,
    line: int,
    line_text: str,
    span: dict[Any, Any],
    depth: int,
    strict: bool,
) -> Value:
    from ._inline import _run_gate

    closer = _run_gate(trimmed, line, line_text, span, depth)
    if closer != len(trimmed) - 1:
        raise_decode(
            "MalformedInlineCompound",
            line,
            line_text,
            span,
            f"Syntax error: Line {line}: MalformedInlineCompound: content after closing delimiter",
            body="content after closing delimiter",
        )
    return parse_inline_value(trimmed, line, line_text, span, depth, strict)


# ---------------------------------------------------------------------------
# Parser frames
# ---------------------------------------------------------------------------


class _Frame:
    """One open Object or Array context (explicit parser stack)."""

    __slots__ = ("explicit", "kind", "opener_byte", "pending_key", "value")

    def __init__(self, kind: str, value: Any, explicit: bool, opener_byte: int) -> None:
        self.kind = kind
        self.value = value
        self.explicit = explicit
        self.pending_key: str | None = None
        self.opener_byte = opener_byte


class _Collecting:
    """An open multi-line string block (§ 5.6)."""

    __slots__ = ("lines", "opener_byte", "verbatim")

    def __init__(self, verbatim: bool, opener_byte: int) -> None:
        self.verbatim = verbatim
        self.lines: list[str] = []
        self.opener_byte = opener_byte

    def terminator(self) -> str:
        return "))" if self.verbatim else ")"


class PlainParser:
    """Line-dispatch parser building plain Python values.

    Subclasses may hook trivia and value attachment;
    :class:`TriviaParser` does exactly that for the ``format`` backend.
    """

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict
        self.stack: list[_Frame] = []
        self.collecting: _Collecting | None = None
        self.root: Any = None
        self.root_consumed = False
        self.multiline_opener: int | None = None

    # -- hooks (default: plain behaviour) ---------------------------------

    def _hook_pair(
        self,
        frame: _Frame,
        key: str,
        value: Value,
        line: int,
        line_text: str,
        span: dict[Any, Any],
    ) -> None:
        insert_value(frame.value, key, value, line, line_text, span)

    def _hook_item(self, frame: _Frame, value: Value, line: int) -> None:
        frame.value.append(value)

    def _hook_open(self, frame: _Frame) -> None:
        pass

    def _hook_comment(self, trimmed: str) -> None:
        pass

    def _hook_blank(self) -> None:
        pass

    def _hook_frame_closed(self, frame: _Frame) -> None:
        pass

    def _hook_inline_root(self, value: Value) -> None:
        pass

    def _hook_pending_key(self) -> None:
        """Trivia capture point at a pair line (TriviaParser overrides)."""

    def _hook_pending_item(self) -> None:
        """Trivia capture point at an array-item line."""

    # -- entry --------------------------------------------------------------

    def parse(self, text: str) -> Any:
        eof = checked_utf8_len(text)
        lines = split_lines(text)
        if text.startswith("﻿") and lines:
            first_text, _ = lines[0]
            lines[0] = (first_text[1:], 3)
        for i, (line_text, byte_start) in enumerate(lines):
            line_num = i + 1
            err_line = line_text[:-1] if line_text.endswith("\r") else line_text
            self.handle_line(
                line_text,
                byte_start,
                line_num,
                err_line,
                _span_for(line_text, byte_start),
            )
        return self.finish(eof)

    # -- line dispatch (§ 5.1) ----------------------------------------------

    def handle_line(
        self,
        raw: str,
        line_start: int,
        line_num: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        if self.collecting is not None:
            trimmed = trim(raw)
            if trimmed == self.collecting.terminator():
                collecting = self.collecting
                self.collecting = None
                self.multiline_opener = None
                self._attach(_finish_multiline(collecting), line_num, err_line, span)
                return
            self.collecting.lines.append(raw)
            return
        trimmed = trim(raw)
        if trimmed == "":
            self._hook_blank()
            return
        if trimmed.startswith("##"):
            self._hook_comment(trimmed)
            return
        if self.root_consumed:
            raise_decode(
                "OrphanLineAfterTopLevelInline",
                line_num,
                err_line,
                span,
                f"Syntax error: Line {line_num}: OrphanLineAfterTopLevelInline:"
                " content after root-level inline compound",
            )
        if self.root is None:
            self._handle_root_line(trimmed, line_num, line_start, err_line, span)
            return
        if trimmed == "}":
            self._close_frame("obj", line_num, err_line, span)
            return
        if trimmed == "]":
            self._close_frame("arr", line_num, err_line, span)
            return
        frame = self.stack[-1]
        if frame.kind == "arr":
            self._array_item_line(trimmed, line_num, line_start, err_line, span)
        else:
            self._pair_line(trimmed, line_num, line_start, err_line, span)

    # -- root detection (§ 5.0.1) ---------------------------------------------

    def _handle_root_line(
        self,
        trimmed: str,
        line_num: int,
        line_start: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        if trimmed == "{":
            self._open_root_frame("obj", line_num, line_start, explicit=True)
            return
        if trimmed == "[":
            self._open_root_frame("arr", line_num, line_start, explicit=True)
            return
        if trimmed[0] in "{[":
            value = _inline_gate(trimmed, line_num, err_line, span, 0, self.strict)
            self.root = value
            self.root_consumed = True
            self._hook_inline_root(value)
            return
        if trimmed[0] in "}]":
            found = trimmed[0]
            expected = "{" if found == "}" else "["
            raise_decode(
                "UnbalancedBracket",
                line_num,
                err_line,
                span,
                f"Syntax error: Line {line_num}: UnbalancedBracket:"
                f" '{found}' without matching '{expected}'",
            )
        scan = scan_unescaped_colon(trimmed)
        if scan.kind == "found":
            prefix = trim_inline(trimmed[: scan.index])
            after = trimmed[scan.index + 1 :]
            pair = bool(prefix) and (
                after.startswith(":") or after == "" or is_inline_whitespace(after[0])
            )
            if pair:
                self._open_root_frame("obj", line_num, line_start, False)
                self._pair_line(trimmed, line_num, line_start, err_line, span)
                return
        self._open_root_frame("arr", line_num, line_start, False)
        self._array_item_line(trimmed, line_num, line_start, err_line, span)

    def _open_root_frame(self, kind: str, line_num: int, line_start: int, explicit: bool) -> None:
        value: Any = {} if kind == "obj" else []
        frame = _Frame(kind, value, explicit, line_start)
        self.root = value
        self.stack.append(frame)
        self._hook_open(frame)

    # -- pair lines (§ 5.3) -----------------------------------------------------

    def _pair_line(
        self,
        trimmed: str,
        line_num: int,
        line_start: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        scan = scan_unescaped_colon(trimmed)
        if scan.kind == "unterminated":
            raise_decode(
                "UnterminatedQuotedKey",
                line_num,
                err_line,
                span,
                f"Syntax error: Line {line_num}: UnterminatedQuotedKey: quoted key"
                " segment not closed on the same line",
            )
        if scan.kind == "absent":
            raise_decode(
                "MissingSeparator",
                line_num,
                err_line,
                span,
                f"Syntax error: Line {line_num}: MissingSeparator: object entries must"
                " be 'key: value' pairs",
            )
        idx = scan.index
        prefix = trimmed[:idx]
        rest = trimmed[idx + 1 :]
        raw_marker = rest.startswith(":")
        after = rest[1:] if raw_marker else rest
        if not prefix.strip(_WS_INLINE):
            _empty_key(line_num, err_line, span)
        if after and not is_inline_whitespace(after[0]):
            raise_decode(
                "MissingSeparatorSpace",
                line_num,
                err_line,
                span,
                f"Syntax error: Line {line_num}: MissingSeparatorSpace: separator must"
                " be followed by whitespace or end of line",
            )
        key_trimmed = trim_inline(prefix)
        self._hook_pending_key()
        self.stack[-1].pending_key = key_trimmed
        if raw_marker:
            value, _ = process_escapes(after.strip(_WS_INLINE), line_num, err_line, span)
            self._attach(value, line_num, err_line, span)
            return
        self._hook_pending_item()
        self._dispatch_value(after.lstrip(_WS_INLINE), line_num, line_start, err_line, span)

    def _dispatch_value(
        self,
        body: str,
        line_num: int,
        line_start: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        kind, payload = classify_value_start(body, line_num, err_line, span, self.strict)
        if kind == "open-obj":
            self._push_frame("obj", line_num, line_start, False)
        elif kind == "open-arr":
            self._push_frame("arr", line_num, line_start, False)
        elif kind == "open-ml":
            self.collecting = _Collecting(False, line_start)
            self.multiline_opener = line_start
        elif kind == "open-mlv":
            self.collecting = _Collecting(True, line_start)
            self.multiline_opener = line_start
        else:
            self._attach(payload, line_num, err_line, span)

    # -- array-item lines (§ 5.4) --------------------------------------------------

    def _array_item_line(
        self,
        trimmed: str,
        line_num: int,
        line_start: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        self._hook_pending_item()
        if trimmed.startswith("::"):
            after = trimmed[2:]
            if after and not is_inline_whitespace(after[0]):
                raise_decode(
                    "MissingSeparatorSpace",
                    line_num,
                    err_line,
                    span,
                    f"Syntax error: Line {line_num}: MissingSeparatorSpace: separator"
                    " must be followed by whitespace or end of line",
                )
            value, _ = process_escapes(after.strip(_WS_INLINE), line_num, err_line, span)
            self._attach(value, line_num, err_line, span)
            return
        self._dispatch_value(trimmed, line_num, line_start, err_line, span)

    # -- frames and attachment --------------------------------------------------------

    def _push_frame(self, kind: str, line_num: int, line_start: int, explicit: bool) -> None:
        frame = _Frame(kind, {} if kind == "obj" else [], explicit, line_start)
        self.stack.append(frame)
        self._hook_open(frame)

    def _attach(self, value: Value, line_num: int, err_line: str, span: dict[Any, Any]) -> None:
        frame = self.stack[-1]
        if frame.kind == "arr":
            self._hook_item(frame, value, line_num)
            return
        key = frame.pending_key
        frame.pending_key = None
        if key is None:
            raise_decode(
                "Other",
                line_num,
                None,
                span,
                f"Line {line_num}: internal error — closed compound without pending key",
            )
        assert key is not None
        self._hook_pair(frame, key, value, line_num, err_line, span)

    def _close_frame(
        self, expected: str, line_num: int, err_line: str, span: dict[Any, Any]
    ) -> None:
        if len(self.stack) <= 1:
            if len(self.stack) == 1 and self.stack[-1].explicit:
                frame = self.stack[-1]
                if frame.kind != expected:
                    self._unbalanced(expected, frame.kind, line_num, err_line, span)
                self.root_consumed = True
                self._hook_frame_closed(frame)
                return
            self._unbalanced(expected, None, line_num, err_line, span)
        frame = self.stack.pop()
        if frame.kind != expected:
            self._unbalanced(expected, frame.kind, line_num, err_line, span)
        self._hook_frame_closed(frame)
        self._attach(frame.value, line_num, err_line, span)

    def _unbalanced(
        self,
        expected: str,
        actual: str | None,
        line_num: int,
        err_line: str,
        span: dict[Any, Any],
    ) -> None:
        found = "}" if expected == "obj" else "]"
        opener = "{" if expected == "obj" else "["
        if actual is not None:
            opener = "{" if actual == "obj" else "["
        raise_decode(
            "UnbalancedBracket",
            line_num,
            err_line,
            span,
            f"Syntax error: Line {line_num}: UnbalancedBracket:"
            f" '{found}' without matching '{opener}'",
        )

    # -- EOF ------------------------------------------------------------------------

    def finish(self, eof_byte: int) -> Any:
        if self.collecting is not None:
            start = self.multiline_opener or 0
            raise_decode(
                "UnclosedCompound",
                None,
                None,
                {"start": start, "end": eof_byte},
                "Unclosed multi-line string at end of input",
            )
        if len(self.stack) > 1 or (
            self.stack and self.stack[-1].explicit and not self.root_consumed
        ):
            frame = self.stack[-1]
            raise_decode(
                "UnclosedCompound",
                None,
                None,
                {"start": frame.opener_byte, "end": eof_byte},
                "Unclosed object at end of input"
                if frame.kind == "obj"
                else "Unclosed array at end of input",
            )
        return self.root if self.root is not None else {}


# ---------------------------------------------------------------------------
# Multi-line strings (§ 5.6)
# ---------------------------------------------------------------------------


def _finish_multiline(collecting: _Collecting) -> str:
    if collecting.verbatim:
        return "\n".join(collecting.lines)
    non_blank = [ln for ln in collecting.lines if trim(ln) != ""]
    prefix = _common_ws_prefix(non_blank)
    out = []
    for ln in collecting.lines:
        if trim(ln) == "":
            out.append("")
        else:
            body = ln[len(prefix) :] if prefix else ln
            out.append(body.rstrip(WS_CHARS))
    return "\n".join(out)


def _leading_ws_run(s: str) -> str:
    end = 0
    n = len(s)
    while end < n and is_inline_whitespace(s[end]):
        end += 1
    return s[:end]


def _common_ws_prefix(lines: list[str]) -> str:
    """Longest leading § 3.3 whitespace prefix shared code-point-wise by.

    every non-blank line (§ 5.6).
    """
    if not lines:
        return ""
    prefix = _leading_ws_run(lines[0])
    for ln in lines[1:]:
        run = _leading_ws_run(ln)
        i = 0
        limit = min(len(prefix), len(run))
        while i < limit and prefix[i] == run[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _span_for(line_text: str, line_start: int) -> dict[Any, Any]:
    trimmed = trim(line_text)
    if not trimmed:
        return {"start": line_start, "end": line_start + byte_len(line_text)}
    lead = len(line_text) - len(line_text.lstrip(_WS_INLINE))
    start = line_start + byte_len(line_text[:lead])
    return {"start": start, "end": start + byte_len(trimmed)}


# ---------------------------------------------------------------------------
# Trivia-carrying parser (the ``format`` backend)
# ---------------------------------------------------------------------------


class TriviaParser(PlainParser):
    """Builds a trivia-carrying tree alongside the plain one.

    Nodes: ``{"k": "obj", "pairs": [(key, trivia, value)], "index":
    {key: position}, "trailing": [...]}`` and ``{"k": "arr", "items":
    [(trivia, value)], "trailing": [...]}``. Leaf slots hold either a
    plain scalar or a nested node
    (registered in ``_tmap`` by the identity of its plain compound). A
    run of two or more blank lines collapses to one, and blank padding
    at the start of a compound is dropped (formatter semantics).
    """

    def __init__(self, strict: bool = False) -> None:
        super().__init__(strict)
        self.pending: Trivia = []
        self.doc_leading: Trivia = []
        self.tstack: list[dict[Any, Any]] = []
        self._tmap: dict[int, dict[Any, Any]] = {}
        self.key_trivia: Trivia = []
        self.item_trivia: Trivia = []

    # -- trivia bookkeeping ------------------------------------------------

    def _take(self) -> Trivia:
        out = self.pending
        self.pending = []
        return out

    def _trim_blanks(self, trivia: Trivia) -> Trivia:
        while trivia and trivia[-1][0]:
            trivia.pop()
        return trivia

    def _at_start(self) -> bool:
        if self.root is None:
            return True
        return not self.stack or len(self.stack[-1].value) == 0

    def _push_blank(self) -> None:
        if not self.pending and self._at_start():
            return
        if self.pending and self.pending[-1][0]:
            return
        self.pending.append((True, ""))

    # -- hooks ---------------------------------------------------------------

    def _hook_blank(self) -> None:
        self._push_blank()

    def _hook_comment(self, trimmed: str) -> None:
        self.pending.append((False, trimmed))

    def _hook_open(self, frame: _Frame) -> None:
        node: dict[Any, Any] = {"k": frame.kind, "trailing": [], "index": {}}
        if frame.kind == "obj":
            node["pairs"] = []
        else:
            node["items"] = []
        self._tmap[id(frame.value)] = node
        self.tstack.append(node)
        if len(self.stack) == 1:
            self.doc_leading = self._take()

    def _wrap(self, value: Value) -> Any:
        if isinstance(value, (dict, list)):
            return self._tmap.get(id(value), value)
        return value

    def _hook_pending_key(self) -> None:
        self.key_trivia = self._take()

    def _hook_pending_item(self) -> None:
        self.item_trivia = self._take()

    def _hook_pair(
        self,
        frame: _Frame,
        key: str,
        value: Value,
        line: int,
        line_text: str,
        span: dict[Any, Any],
    ) -> None:
        insert_value(frame.value, key, value, line, line_text, span)
        trivia = self.key_trivia
        self.key_trivia = []
        t_insert(self.tstack[-1], key, trivia, self._wrap(value))

    def _hook_item(self, frame: _Frame, value: Value, line: int) -> None:
        frame.value.append(value)
        trivia = self.item_trivia
        self.item_trivia = []
        self.tstack[-1]["items"].append((trivia, self._wrap(value)))

    def _hook_frame_closed(self, frame: _Frame) -> None:
        node = self.tstack.pop()
        node["trailing"].extend(self._trim_blanks(self._take()))

    def _hook_inline_root(self, value: Value) -> None:
        self.doc_leading = self._take()

    # -- result ---------------------------------------------------------------

    def finish(self, eof_byte: int) -> Any:
        super().finish(eof_byte)  # shared EOF validation
        eof_trivia = self._trim_blanks(self._take())
        if not self.tstack:
            # Inline root (or content-free document): rebuild the node
            # from the plain tree — a comment can never occur inside an
            # inline compound, so the copy carries no trivia of its own.
            node = _plain_to_node(self.root if self.root is not None else {})
            node["trailing"].extend(eof_trivia)
        else:
            node = self.tstack.pop()
            node["trailing"].extend(eof_trivia)
        return {"leading": self.doc_leading, "root": node}


def _plain_to_node(value: Any) -> dict[Any, Any]:
    """Rebuild a trivia node from the plain tree (iterative, no input-depth recursion)."""
    if isinstance(value, dict):
        root: dict[Any, Any] = {"k": "obj", "pairs": [], "trailing": [], "index": {}}
    else:
        root = {"k": "arr", "items": [], "trailing": []}
    stack: list[tuple[Any, dict[Any, Any]]] = [(value, root)]
    while stack:
        val, node = stack.pop()
        if isinstance(val, dict):
            pairs: list[Any] = node["pairs"]
            index: dict[Any, Any] = node["index"]
            for k, v in val.items():
                if isinstance(v, (dict, list)):
                    child: dict[Any, Any] = (
                        {"k": "obj", "pairs": [], "trailing": [], "index": {}}
                        if isinstance(v, dict)
                        else {"k": "arr", "items": [], "trailing": []}
                    )
                    pairs.append((k, [], child))
                    index[k] = len(pairs) - 1
                    stack.append((v, child))
                else:
                    pairs.append((k, [], v))
                    index[k] = len(pairs) - 1
            continue
        items: list[Any] = node["items"]
        for v in val:
            if isinstance(v, (dict, list)):
                child = (
                    {"k": "obj", "pairs": [], "trailing": [], "index": {}}
                    if isinstance(v, dict)
                    else {"k": "arr", "items": [], "trailing": []}
                )
                items.append(([], child))
                stack.append((v, child))
            else:
                items.append(([], v))
    return root


def t_insert(node: dict[Any, Any], path_text: str, trivia: Trivia, value: Any) -> None:
    """Insert into the trivia tree; the leaf pair carries ``trivia``.

    The plain tree has already validated the path, so this mirrors only
    the descend/merge shape of :func:`insert_value`. Each object node
    keeps an insertion-ordered ``index`` (decoded key → position in
    ``pairs``) so lookups are O(1) per segment.
    """
    segments = [path_text] if key_is_single_segment(path_text) else split_key_path(path_text)
    cur = node
    pairs: list[Any] = cur["pairs"]
    index: dict[Any, Any] = cur["index"]
    for idx, raw_seg in enumerate(segments):
        decoded = decode_key_segment(trim_inline(raw_seg), 0, "", {"start": 0, "end": 0})
        if idx + 1 == len(segments):
            pos = index.get(decoded)
            if pos is not None:
                entry = pairs[pos]
                pairs[pos] = (entry[0], entry[1], value)
            else:
                pairs.append((decoded, trivia, value))
                index[decoded] = len(pairs) - 1
            return
        pos = index.get(decoded)
        if pos is not None:
            v = pairs[pos][2]
            if isinstance(v, dict) and "k" in v:
                cur = v
            else:
                child: dict[Any, Any] = {"k": "obj", "pairs": [], "trailing": [], "index": {}}
                entry = pairs[pos]
                pairs[pos] = (entry[0], entry[1], child)
                cur = child
        else:
            child = {"k": "obj", "pairs": [], "trailing": [], "index": {}}
            pairs.append((decoded, [], child))
            index[decoded] = len(pairs) - 1
            cur = child
        pairs = cur["pairs"]
        index = cur["index"]


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def parse_document(text: str, strict: bool = False) -> Any:
    """Parse ``text`` into plain Python values (``loads`` backend)."""
    return PlainParser(strict).parse(text)


def parse_with_trivia(text: str, strict: bool = False) -> dict[Any, Any]:
    """Parse ``text`` into a trivia-carrying document (``format``)."""
    doc: dict[Any, Any] = TriviaParser(strict).parse(text)
    return doc

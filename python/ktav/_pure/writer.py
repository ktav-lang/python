"""The canonical and pretty writers for the pure-Python backend.

A byte-exact port of the Rust core's render layer (spec § 5.9).

Both the plain (``dumps``-style, prefers readable indented stripped
multi-line strings) and canonical (``emit_canonical``-style, prefers
verbatim) modes are implemented, mirroring
``ktav::render::{render, emit_canonical}`` exactly, including the
§ 5.9.3 top-level Array wrap, the § 5.9.10 key form selection, the
§ 5.9.6/§ 5.9.12 first-item safeguards, and the seven § 5.9.0
representability rejections.

Cost model: a render pass is linear in the OUTPUT bytes it produces
and O(1) per value node; indentation is emitted per line through the
``_SPACES`` chunk helper. No claim of input-byte linearity is made —
deep nesting costs per nesting level, not per input byte.
"""

from __future__ import annotations

from typing import Any

from ._inline import Value
from ._keys import is_pair_shape
from ._numbers import canonical_float
from ._text import validate_utf8
from .errors import KtavEncodeError, raise_encode_reason
from .parser import parse_document, parse_with_trivia

__all__ = [
    "canonical_from_source",
    "dumps",
    "dumps_force_strings",
    "emit_canonical",
    "format",
]

_INDENT = "    "
_SPACES = " " * 64


# ---------------------------------------------------------------------------
# Value conversion (mirrors the native binding's py_to_value)
# ---------------------------------------------------------------------------


def to_value(obj: Any, path: list[str] | None = None) -> Value:
    """Map a native Python object to the internal Value model.

    Applies the same rejections as the Rust binding's ``py_to_value``.
    Iterative over input-controlled depth with an active-path cycle
    detector (an ``id()`` set of containers on the current path): a
    cycle raises ``KtavEncodeError`` with ``error="Message"``, never
    :class:`RecursionError`.
    """
    if obj is None:
        return None
    if obj is True or obj is False:
        return obj
    if isinstance(obj, bool):  # pragma: no cover — covered above
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            raise_encode_reason("NonFiniteFloat")
        return obj
    if isinstance(obj, str):
        return obj
    if not isinstance(obj, (list, tuple, dict)):
        name = type(obj).__name__
        raise KtavEncodeError(f"Unsupported Python type for Ktav: {name}", error="Message")

    on_path: set[int] = set()
    root: Value = [None] * len(obj) if isinstance(obj, (list, tuple)) else {}
    stack: list[tuple[bool, Any, Value]] = [(False, obj, root)]
    while stack:
        leave, src, dst = stack.pop()
        if leave:
            on_path.discard(id(src))
            continue
        on_path.add(id(src))
        # Push the leave marker first so it runs after every child.
        stack.append((True, src, dst))
        if isinstance(src, (list, tuple)):
            for i in range(len(src) - 1, -1, -1):
                child = _to_value_step(src[i], on_path, stack)
                dst[i] = child
        else:
            for key, val in src.items():
                if not isinstance(key, str):
                    raise KtavEncodeError("Object keys must be strings", error="Message")
                dst[key] = _to_value_step(val, on_path, stack)
    return root


def _to_value_step(item: Any, on_path: set[int], stack: list[Any]) -> Value:
    """Convert one scalar, or enqueue one container copy for traversal."""
    if item is None or item is True or item is False or isinstance(item, (bool, int, str)):
        return item
    if isinstance(item, float):
        if item != item or item in (float("inf"), float("-inf")):
            raise_encode_reason("NonFiniteFloat")
        return item
    if isinstance(item, (list, tuple, dict)):
        if id(item) in on_path:
            raise KtavEncodeError("Cannot serialize a cyclic container to Ktav", error="Message")
        fresh: Value = [None] * len(item) if isinstance(item, (list, tuple)) else {}
        stack.append((False, item, fresh))
        return fresh
    name = type(item).__name__
    raise KtavEncodeError(f"Unsupported Python type for Ktav: {name}", error="Message")


# ---------------------------------------------------------------------------
# String form helpers (§ 5.9.5 / § 5.9.6 / § 5.9.7)
# ---------------------------------------------------------------------------


def _string_needs_multiline(s: str) -> bool:
    if s and (s[0] in _WS_ALL or s[-1] in _WS_ALL):
        return True
    return any(ord(ch) < 0x20 and ch != "\t" for ch in s)


_WS_ALL = "".join(
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
_WS_INLINE = _WS_ALL.replace("\n", "").replace("\r", "")


def _ws_trim(s: str) -> str:
    return s.strip(_WS_ALL)


def _ws_trim_inline(s: str) -> str:
    return s.strip(_WS_INLINE)


def _needs_raw_marker(s: str) -> bool:

    if not s:
        return False
    first = s[0]
    if first in " \t\x0b\x0c":
        t = s.lstrip(_WS_INLINE)
        return t.startswith(("{", "[")) or _needs_raw_marker_content(t)
    if first in "{[":
        return True
    return _needs_raw_marker_content(s)


def _needs_raw_marker_content(s: str) -> bool:
    if s in ("null", "true", "false", "(", "((", "()", "(())"):
        return True
    from ._numbers import is_float_literal, is_integer_grammar

    return is_integer_grammar(s) or is_float_literal(s)


def _item_needs_raw_marker(s: str) -> bool:
    return _needs_raw_marker(s) or s.startswith(("##", "::")) or s in ("]", "}")


def _multiline_form(s: str, prefer_stripped: bool, path: list[str] | None) -> str:
    """Pick ``"verbatim"`` or ``"stripped"``, or raise a § 5.9.7 code.

    ``path`` names the offending node in the raised error.
    """
    sole_single = sole_double = ws_only = indented = trailing_ws = False
    for line in s.split("\n"):
        trimmed = line.strip(_WS_INLINE)
        if trimmed == ")":
            sole_single = True
        elif trimmed == "))":
            sole_double = True
        if not line:
            continue
        if not trimmed:
            ws_only = True
        elif line[0] in _WS_INLINE:
            indented = True
        if line.rstrip(_WS_INLINE) != line:
            trailing_ws = True
    stripped_safe = not (sole_single or ws_only or indented or trailing_ws)
    verbatim_ok = not sole_double
    if prefer_stripped and stripped_safe:
        return "stripped"
    if verbatim_ok:
        return "verbatim"
    has_common_indent = _common_ws_prefix(s.split("\n")) != ""
    stripped_lossless = not (sole_single or ws_only or has_common_indent or trailing_ws)
    if stripped_lossless:
        return "stripped"
    if sole_single:
        raise_encode_reason("BothFormsRequired", path)
    if trailing_ws:
        raise_encode_reason("TrailingWhitespaceCollision", path)
    raise_encode_reason("LeadingWhitespaceCollision", path)


def _common_ws_prefix(lines: list[str]) -> str:
    non_blank = [ln for ln in lines if ln.strip(_WS_ALL) != ""]
    if not non_blank:
        return ""

    def run(s: str) -> str:
        end = 0
        while end < len(s) and s[end] in _WS_ALL:
            end += 1
        return s[:end]

    prefix = run(non_blank[0])
    for ln in non_blank[1:]:
        other = run(ln)
        i = 0
        limit = min(len(prefix), len(other))
        while i < limit and prefix[i] == other[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix


# ---------------------------------------------------------------------------
# Key emission (§ 5.9.10)
# ---------------------------------------------------------------------------

_EDGE_WS_QUOTED_ADMITS = _WS_INLINE  # quoted segments admit these raw


def _is_ktav_ws(ch: str) -> bool:
    return ch in _WS_ALL


def push_key_segment(key: str, root_first_key: bool, out: list[str]) -> None:
    first = key[:1]
    if first in ('"', "'", "`") or (root_first_key and first == "﻿") or key.startswith("##"):
        _push_quoted_key(key, out)
        return
    if key and ((key[0] in _EDGE_WS_QUOTED_ADMITS) or (key[-1] in _EDGE_WS_QUOTED_ADMITS)):
        _push_quoted_key(key, out)
        return
    needs_rewrite = False
    for ch in key:
        if ch in ".:,{}[]()":
            _push_quoted_key(key, out)
            return
        if ch in "\\\n\r" or ord(ch) == 0x7F or (ord(ch) < 0x20 and ch not in "\t\v\f"):
            needs_rewrite = True
    if needs_rewrite:
        _push_bare_key_escaped(key, out)
    else:
        out.append(key)


def _push_unicode_escape(out: list[str], ch: str) -> None:
    out.append(f"\\u{ord(ch):04X}")


def _push_bare_key_escaped(key: str, out: list[str]) -> None:
    last_idx = len(key) - 1
    for i, ch in enumerate(key):
        at_edge = i == 0 or i == last_idx
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif _is_ktav_ws(ch):
            if at_edge:
                _push_unicode_escape(out, ch)
            else:
                out.append(ch)
        elif ch == ".":
            out.append("\\.")
        elif ch == ":":
            out.append("\\:")
        elif ch == ",":
            out.append("\\,")
        elif ch == "{":
            out.append("\\{")
        elif ch == "}":
            out.append("\\}")
        elif ch == "[":
            out.append("\\[")
        elif ch == "]":
            out.append("\\]")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            _push_unicode_escape(out, ch)
        else:
            out.append(ch)


def _push_quoted_key(key: str, out: list[str]) -> None:
    out.append('"')
    for ch in key:
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif (ord(ch) < 0x20 and ch not in "\t\v\f") or ord(ch) == 0x7F:
            _push_unicode_escape(out, ch)
        else:
            out.append(ch)
    out.append('"')


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------


class _Renderer:
    """Shared iterative emitter for all writer modes.

    ``canonical`` selects the § 5.9 verbatim-preferring multi-line
    choice; ``force`` selects the everything-is-a-String mode.
    Traversal runs on an explicit task stack — no recursion on
    input-controlled depth. Work is O(output bytes) plus O(1) per
    node; indentation is emitted per line via the ``_SPACES`` chunk
    helper (linear in the indent text actually written, not claimed
    linear in input bytes).
    """

    def __init__(self, canonical: bool, force: bool, out: list[str]) -> None:
        self.canonical = canonical
        self.force = force
        self.out = out
        self.path: list[str] = []

    def indent(self, level: int) -> None:
        remaining = level * 4
        while remaining > 0:
            chunk = min(remaining, len(_SPACES))
            self.out.append(_SPACES[:chunk])
            remaining -= chunk

    def fail(self, reason: str) -> None:
        # The § 5.9.0 walk visits nodes in document order, so the first
        # failure is the innermost offending node; ``path`` is raised
        # as-is (never cleared), mirroring the Rust crate's ``at_path``.
        raise_encode_reason(reason, list(self.path))

    # -- task-stack traversal ---------------------------------------------
    # Tasks: ("emit", text) | ("indent", level) | ("poppath",)
    #      | ("pair", key, value, indent, root_first_key)
    #      | ("value", value, indent)
    #      | ("item", value, indent, is_root_array_first)
    #      | ("body", obj, indent, is_root)

    def _run(self, stack: list[tuple[Any, ...]]) -> None:
        out = self.out
        while stack:
            task = stack.pop()
            tag = task[0]
            if tag == "emit":
                out.append(task[1])
            elif tag == "indent":
                self.indent(task[1])
            elif tag == "poppath":
                self.path.pop()
            elif tag == "pair":
                _, key, value, level, root_first = task
                # Rust parity: the key is pushed verbatim (never split
                # on dots) BEFORE the empty-key check, so EmptyKeyName
                # carries the trailing "" segment (representable.rs).
                self.path.append(key)
                if key == "":
                    self.fail("EmptyKeyName")
                self.indent(level)
                push_key_segment(key, root_first, out)
                if self.force:
                    text = _forced_string_text(value)
                    if text is not None:
                        self.string_in_pair(text, level)
                        self.path.pop()
                        continue
                stack.append(("poppath",))
                stack.append(("value", value, level))
            elif tag == "value":
                self._emit_pair_value(task[1], task[2], stack)
            elif tag == "item":
                _, value, level, root_first = task
                self.indent(level)
                if self.force:
                    text = _forced_string_text(value)
                    if text is not None:
                        self.string_as_item(text, level, root_first)
                        continue
                self._emit_item(value, level, root_first, stack)
            else:  # "body"
                _, obj, level, is_root = task
                items = list(obj.items())
                for index in range(len(items) - 1, -1, -1):
                    key, value = items[index]
                    stack.append(("pair", key, value, level, is_root and index == 0))

    def render_object_body(self, obj: dict[Any, Any], indent: int, is_root: bool) -> None:
        self._run([("body", obj, indent, is_root)])

    def render_pair(self, key: str, value: Value, indent: int, root_first_key: bool) -> None:
        self._run([("pair", key, value, indent, root_first_key)])

    def _emit_pair_value(self, value: Value, indent: int, stack: list[tuple[Any, ...]]) -> None:
        out = self.out
        if value is None:
            out.append(": null\n")
        elif value is True or value is False:
            out.append(": true\n" if value else ": false\n")
        elif isinstance(value, str):
            self.string_in_pair(value, indent)
        elif isinstance(value, float):
            out.append(": ")
            out.append(self.float_text(value))
            out.append("\n")
        elif isinstance(value, int):
            out.append(": ")
            out.append(str(value))
            out.append("\n")
        elif isinstance(value, list):
            if not value:
                out.append(": []\n")
            else:
                out.append(": [\n")
                # Rust parity: array items add NO path segment — the
                # innermost object pair's key path is reported as-is
                # (representable.rs `check_node`).
                # LIFO order: push closer, its indent, then items in
                # REVERSE index order so item 0 pops first.
                stack.append(("emit", "]\n"))
                stack.append(("indent", indent))
                for index in range(len(value) - 1, -1, -1):
                    stack.append(  # noqa: PERF401
                        ("item", value[index], indent + 1, False)
                    )
        else:  # dict[Any, Any]
            if not value:
                out.append(": {}\n")
            else:
                out.append(": {\n")
                stack.append(("emit", "}\n"))
                stack.append(("indent", indent))
                stack.append(("body", value, indent + 1, False))

    def float_text(self, value: float) -> str:
        if self.canonical:
            return canonical_float(value)
        return _pretty_float(value)

    def render_item(self, value: Value, indent: int, is_root_array_first: bool) -> None:
        self._run([("item", value, indent, is_root_array_first)])

    def _emit_item(
        self, value: Value, indent: int, is_root_array_first: bool, stack: list[tuple[Any, ...]]
    ) -> None:
        out = self.out
        if value is None:
            out.append("null\n")
        elif value is True or value is False:
            out.append("true\n" if value else "false\n")
        elif isinstance(value, str):
            self.string_as_item(value, indent, is_root_array_first)
        elif isinstance(value, float):
            out.append(self.float_text(value))
            out.append("\n")
        elif isinstance(value, int):
            out.append(str(value))
            out.append("\n")
        elif isinstance(value, list):
            if not value:
                out.append("[]\n")
            else:
                out.append("[\n")
                stack.append(("emit", "]\n"))
                stack.append(("indent", indent))
                for index in range(len(value) - 1, -1, -1):
                    stack.append(  # noqa: PERF401
                        ("item", value[index], indent + 1, False)
                    )
        else:  # dict[Any, Any]
            if not value:
                out.append("{}\n")
            else:
                out.append("{\n")
                stack.append(("emit", "}\n"))
                stack.append(("indent", indent))
                stack.append(("body", value, indent + 1, False))

    # -- Strings ---------------------------------------------------------

    def string_in_pair(self, s: str, indent: int) -> None:
        if "\r" in s:
            self.fail("CRByte")
        if _string_needs_multiline(s):
            self.multiline_string(s, indent, True)
            return
        if s == "":
            self.out.append(":\n")
            return
        if _needs_raw_marker(s):
            self.out.append(":: ")
        else:
            self.out.append(": ")
        self.out.append(s)
        self.out.append("\n")

    def string_as_item(self, s: str, indent: int, is_root_array_first: bool) -> None:
        if "\r" in s:
            self.fail("CRByte")
        if _string_needs_multiline(s):
            self.multiline_string(s, indent, False)
            return
        if s == "":
            self.out.append("::\n")
            return
        if _item_needs_raw_marker(s) or (
            is_root_array_first and (is_pair_shape(s) or s.startswith("﻿"))
        ):
            self.out.append(":: ")
        self.out.append(s)
        self.out.append("\n")

    def multiline_string(self, s: str, indent: int, is_pair: bool) -> None:
        # Representability: the collision checks run through the shared
        # chooser in both modes; a rejection surfaces the § 5.9.0 code.
        if self.canonical:
            form = _multiline_form(s, False, self.path)
        else:
            form = _choose_multiline_pretty(s, self.path)
        if form == "verbatim":
            self.out.append(": ((\n" if is_pair else "((\n")
            self.out.append(s)
            self.out.append("\n")
            self.indent(indent)
            self.out.append("))\n")
        else:
            self.out.append(": (\n" if is_pair else "(\n")
            self.out.append(s)
            self.out.append("\n")
            self.indent(indent)
            self.out.append(")\n")


def _choose_multiline_pretty(s: str, path: list[str] | None) -> str:
    """Pick the pretty writers' multi-line form for ``s``.

    Unconditionally-safe stripped when possible, verbatim otherwise,
    and the chooser's error set when neither form can hold the body
    (§ 5.6.1).
    """
    sole_single = ws_only = indented = trailing_ws = False
    for line in s.split("\n"):
        trimmed = line.strip(_WS_INLINE)
        if trimmed == ")":
            sole_single = True
        if not line:
            continue
        if not trimmed:
            ws_only = True
        elif line[0] in _WS_INLINE:
            indented = True
        if line.rstrip(_WS_INLINE) != line:
            trailing_ws = True
    stripped_safe = not (sole_single or ws_only or indented or trailing_ws)
    if stripped_safe:
        return "stripped"
    return _multiline_form(s, False, path)


def _forced_string_text(value: Value) -> str | None:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return _pretty_float(value)
    if isinstance(value, int):
        return str(value)
    return None


def _pretty_float(value: float) -> str:
    """The native binding's ``format_float`` over Python's ``repr``.

    Shortest round-trip digits with a mandatory decimal point. (The
    canonical writer never uses this; see :func:`canonical_float`,
    which is what the corpus's ``*.canonical.ktav`` oracles pin.)
    """
    r = repr(value)
    e_pos = r.find("e")
    if e_pos >= 0:
        if "." not in r[:e_pos]:
            r = r[:e_pos] + ".0" + r[e_pos:]
        return r
    if "." not in r:
        return r + ".0"
    return r


# ---------------------------------------------------------------------------
# Document roots (§ 5.9.3)
# ---------------------------------------------------------------------------


def render_document(value: Any, canonical: bool, force: bool) -> str:
    if not isinstance(value, (dict, list)):
        raise_encode_reason("ScalarRoot")
    out: list[str] = []
    renderer = _Renderer(canonical, force, out)
    if isinstance(value, dict):
        renderer.render_object_body(value, 0, True)
    elif not value:
        out.append("[]\n")
    elif isinstance(value[0], (dict, list)):
        out.append("[\n")
        for item in value:
            renderer.render_item(item, 1, False)
        out.append("]\n")
    else:
        for index, item in enumerate(value):
            renderer.render_item(item, 0, index == 0)
    return "".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _check_root(obj: Any) -> Value:
    value = to_value(obj)
    if not isinstance(value, (dict, list)):
        raise_encode_reason("ScalarRoot")
    return value


def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string (native semantics)."""
    return render_document(_check_root(obj), canonical=False, force=False)


def emit_canonical(obj: Any) -> str:
    """Emit the canonical (§ 5.9) form of ``obj``."""
    return render_document(_check_root(obj), canonical=True, force=False)


def dumps_force_strings(obj: Any) -> str:
    """Serialize ``obj`` with every scalar coerced to a String."""
    return render_document(_check_root(obj), canonical=False, force=True)


def canonical_from_source(s: str) -> str:
    """Parse ``s`` and emit its canonical form.

    Text in, canonical text out; the value never becomes a
    Python-visible object on the way.
    """
    value = parse_document(_input_text(s), strict=False)
    return render_document(value, canonical=True, force=False)


def format(s: str) -> str:
    """Format a Ktav document: text in, normalised text out.

    Comments and blank-line grouping survive; structure is canonical
    (§ 5.9); the transform is a fixed point.
    """
    from ._formatter import emit_formatted

    doc = parse_with_trivia(_input_text(s), strict=False)
    return emit_formatted(doc)


def _input_text(s: str | bytes | bytearray | memoryview) -> str:
    """Accept ``str`` or UTF-8 ``bytes`` (§ 6.15 validation first)."""
    if isinstance(s, (bytes, bytearray, memoryview)):
        return validate_utf8(bytes(s))
    return s

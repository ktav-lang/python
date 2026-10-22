"""Comment-preserving formatter (``format``).

A port of the Rust core's ``ktav::format_str``.

Reuses the canonical writer's string/key/number emission unchanged;
the only addition is flushing each preserved trivia run (comments and
blank lines, § 3.4: a comment owns a whole line) immediately before
the construct it is attached to.
"""

from __future__ import annotations

from typing import Any

from .writer import _Renderer, push_key_segment

__all__ = ["emit_formatted"]


def _emit_trivia(trivia: list[Any], indent: int, out: list[str]) -> None:
    for is_blank, text in trivia:
        if is_blank:
            out.append("\n")
        else:
            _push_indent(out, indent)
            out.append(text)
            out.append("\n")


def _push_indent(out: list[str], level: int) -> None:
    out.append(" " * (level * 4))


def emit_formatted(doc: dict[Any, Any]) -> str:
    out: list[str] = []
    _emit_trivia(doc["leading"], 0, out)
    renderer = _TRenderer(out)
    renderer.root(doc["root"])
    return "".join(out)


class _TRenderer(_Renderer):
    """The canonical renderer over trivia-carrying nodes.

    Nodes: ``{"k": "obj", "pairs": [(key, trivia, value)], "index":
    {...}, "trailing": [...]}`` / ``{"k": "arr", "items": [(trivia,
    value)], "trailing": [...]}``; leaf values are plain scalars.
    Traversal runs on an explicit task stack — no recursion on
    input-controlled depth; O(output bytes).
    """

    def __init__(self, out: list[str]) -> None:
        super().__init__(True, False, out)
        self.path = []

    def root(self, node: dict[Any, Any]) -> None:
        if node["k"] == "obj":
            self._run_t([("tobj", node, 0, True)])
            return
        items = node["items"]
        trailing = node["trailing"]
        if not items and not trailing:
            # § 5.9.3: empty Array root → `[]\n` (mirrors formatted.rs).
            self.out.append("[]\n")
            return
        first_is_compound = bool(items) and isinstance(items[0][1], dict)
        needs_wrap = first_is_compound or (not items and bool(trailing))
        if needs_wrap:
            self.out.append("[\n")
            self._run_t([("tarr", node, 1)])
            self.out.append("]\n")
            return
        stack: list[tuple[Any, ...]] = []
        for index in range(len(items) - 1, -1, -1):
            stack.append(("titem", items[index][1], 0, index == 0))
            stack.append(("trivia", items[index][0], 0))
        stack.append(("trivia", trailing, 0))
        self._run_t(stack)

    # -- task-stack traversal ------------------------------------------------
    # Extra tasks: ("trivia", trivia, indent) | ("tobj", node, indent, is_root)
    #            | ("tarr", node, indent) | ("tpair", key, value, indent, first)
    #            | ("titem", value, indent, is_root_array_first)

    def _run_t(self, stack: list[tuple[Any, ...]]) -> None:
        out = self.out
        while stack:
            task = stack.pop()
            tag = task[0]
            if tag == "trivia":
                _emit_trivia(task[1], task[2], out)
            elif tag == "tobj":
                _, node, indent, is_root = task
                stack.append(("trivia", node["trailing"], indent))
                pairs = node["pairs"]
                for index in range(len(pairs) - 1, -1, -1):
                    key, trivia, value = pairs[index]
                    stack.append(("tpair", key, value, indent, is_root and index == 0))
                    stack.append(("trivia", trivia, indent))
            elif tag == "tarr":
                _, node, indent = task
                stack.append(("trivia", node["trailing"], indent))
                items = node["items"]
                for index in range(len(items) - 1, -1, -1):
                    stack.append(("titem", items[index][1], indent, False))
                    stack.append(("trivia", items[index][0], indent))
            elif tag == "tpair":
                _, key, value, indent, root_first = task
                # Rust parity: verbatim key, pushed before the empty-key
                # check so EmptyKeyName carries the trailing "" segment.
                self.path.append(key)
                if key == "":
                    self.fail("EmptyKeyName")
                self.indent(indent)
                push_key_segment(key, root_first, out)
                if isinstance(value, dict) and "k" in value:
                    if value["k"] == "obj":
                        if not value["pairs"] and not value["trailing"]:
                            out.append(": {}\n")
                            self.path.pop()
                            continue
                        out.append(": {\n")
                        stack.append(("emit", "}\n"))
                        stack.append(("indent", indent))
                        stack.append(("poppath",))
                        stack.append(("tobj", value, indent + 1, False))
                    else:
                        if not value["items"] and not value["trailing"]:
                            out.append(": []\n")
                            self.path.pop()
                            continue
                        out.append(": [\n")
                        stack.append(("emit", "]\n"))
                        stack.append(("indent", indent))
                        stack.append(("poppath",))
                        stack.append(("tarr", value, indent + 1))
                    continue
                stack.append(("poppath",))
                stack.append(("value", value, indent))
            else:  # "titem"
                _, value, indent, is_root_array_first = task
                if isinstance(value, dict) and "k" in value:
                    self.indent(indent)
                    if value["k"] == "obj":
                        if not value["pairs"] and not value["trailing"]:
                            out.append("{}\n")
                            continue
                        out.append("{\n")
                        stack.append(("emit", "}\n"))
                        stack.append(("indent", indent))
                        stack.append(("tobj", value, indent + 1, False))
                    else:
                        if not value["items"] and not value["trailing"]:
                            out.append("[]\n")
                            continue
                        out.append("[\n")
                        stack.append(("emit", "]\n"))
                        stack.append(("indent", indent))
                        stack.append(("tarr", value, indent + 1))
                    continue
                self._run([("item", value, indent, is_root_array_first)])

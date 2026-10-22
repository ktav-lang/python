"""Trivia-tree insertion helpers (the ``format`` backend).

Internal trivia nodes are ordinary ``dict`` objects carrying user keys
under reserved field names (``k``/``pairs``/``items``/``index``/
``trailing``). Because all of those strings are also legal user keys,
the sole type tag is the private :data:`_NODE_TAG` sentinel — a plain
user object such as ``{"k": 1}`` never carries it and is never mistaken
for a trivia node.
"""

from __future__ import annotations

from typing import Any

from ._keys import decode_key_segment, key_is_single_segment, split_key_path
from ._text import trim_inline

__all__ = ["Trivia", "t_insert", "t_insert_decoded"]

Trivia = list[tuple[bool, str]]  # (is_blank, text)

# Internal trivia node: heterogeneous values (pairs/index/trailing/...).
# Nodes are keyed by the private ``_NODE_TAG`` sentinel (an ``object``)
# PLUS string field names (``k``/``pairs``/``index``/...), so the honest
# key type is ``object`` — NOT ``str``. Index READS like ``node["k"]``
# / ``node["index"]`` remain fine under ``object`` keys. Plain user
# inline objects (``dict[str, Any]``) are NOT TriviaNodes: they never
# carry the sentinel. ``TriviaIndex`` types the ``index`` field so index
# lookups return ``int | None`` rather than ``Any``.
TriviaNode = dict[object, Any]
TriviaIndex = dict[str, int]

# Module-private sentinel: presence marks a node as an internal trivia
# node (never a plain user inline object).
_NODE_TAG = object()


def t_insert(node: TriviaNode, path_text: str, trivia: Trivia, value: Any) -> None:
    """Decode ``path_text`` and insert into the trivia tree.

    The plain tree has already validated the path, so this mirrors only
    the descend/merge shape of :func:`~._keys.insert_value`. Each object
    node keeps an insertion-ordered ``index`` (decoded key → position in
    ``pairs``) so lookups are O(1) per segment.
    """
    segments = [path_text] if key_is_single_segment(path_text) else split_key_path(path_text)
    decoded = [
        decode_key_segment(trim_inline(raw_seg), 0, "", {"start": 0, "end": 0})
        for raw_seg in segments
    ]
    t_insert_decoded(node, decoded, trivia, value)


def _index_lookup(node: TriviaNode, key: str) -> int | None:
    """Single lookup point for the trivia index (test hook: countable)."""
    index: TriviaIndex = node["index"]
    return index.get(key)


def _adopt(value: dict[Any, Any] | list[Any]) -> TriviaNode:
    """Convert a plain compound into a tagged trivia node.

    Preserves all entries (insertion order), descendants, and an index
    coherent with the appended pairs.

    Mirrors ``parser._plain_to_node`` (duplicated because parser imports
    from this module — importing back would be circular), but unlike that
    helper the ROOT is always tagged, matching every other creation site.
    """
    if isinstance(value, dict):
        root: TriviaNode = {
            _NODE_TAG: True,
            "k": "obj",
            "pairs": [],
            "trailing": [],
            "index": {},
        }
    else:
        root = {_NODE_TAG: True, "k": "arr", "items": [], "trailing": []}
    stack: list[tuple[Any, TriviaNode]] = [(value, root)]
    while stack:
        val, node = stack.pop()
        if isinstance(val, dict):
            pairs: list[Any] = node["pairs"]
            index: TriviaIndex = node["index"]
            for k, v in val.items():
                if isinstance(v, (dict, list)):
                    child: TriviaNode = (
                        {_NODE_TAG: True, "k": "obj", "pairs": [], "trailing": [], "index": {}}
                        if isinstance(v, dict)
                        else {_NODE_TAG: True, "k": "arr", "items": [], "trailing": []}
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
                    {_NODE_TAG: True, "k": "obj", "pairs": [], "trailing": [], "index": {}}
                    if isinstance(v, dict)
                    else {_NODE_TAG: True, "k": "arr", "items": [], "trailing": []}
                )
                items.append(([], child))
                stack.append((v, child))
            else:
                items.append(([], v))
    return root


def t_insert_decoded(
    node: TriviaNode, decoded_segments: list[str], trivia: Trivia, value: Any
) -> None:
    """Insert at an already-decoded path (see :func:`t_insert`).

    ``decoded_segments`` is produced once — by the dry-run
    :func:`~._keys._insert_walk` preflight in ``TriviaParser._hook_pair``,
    in the same order the plain tree validates them.
    """
    cur: TriviaNode = node
    pairs: list[Any] = cur["pairs"]
    index: TriviaIndex = cur["index"]
    for idx, decoded in enumerate(decoded_segments):
        if idx + 1 == len(decoded_segments):
            pos = _index_lookup(cur, decoded)
            if pos is not None:
                entry = pairs[pos]
                pairs[pos] = (entry[0], entry[1], value)
            else:
                pairs.append((decoded, trivia, value))
                index[decoded] = len(pairs) - 1
            return
        pos = _index_lookup(cur, decoded)
        if pos is not None:
            v = pairs[pos][2]
            if isinstance(v, dict) and _NODE_TAG in v:
                if "pairs" not in v:
                    # Tagged ARRAY node: unreachable after the _hook_pair
                    # dry-run preflight (a list blocks the path with
                    # KeyPathConflict before the trivia tree is touched).
                    raise AssertionError("trivia descent into non-object node")
                cur = v
            elif isinstance(v, (dict, list)):
                # Plain inline compound (e.g. ``a: {x: 1}`` reopened by
                # ``a.y: 2``): adopt it — convert to a tagged node that
                # keeps the existing entries — instead of dropping them.
                # A scalar can never reach here: insert_value raises
                # KeyPathConflict when a scalar blocks a descend path in
                # the plain tree, so plain insertion would already have
                # failed. Defensive fallback below keeps the old
                # fresh-empty behavior for that impossible case.
                child = _adopt(v)
                entry = pairs[pos]
                pairs[pos] = (entry[0], entry[1], child)
                cur = child
            else:
                child: TriviaNode = {
                    _NODE_TAG: True,
                    "k": "obj",
                    "pairs": [],
                    "trailing": [],
                    "index": {},
                }
                entry = pairs[pos]
                pairs[pos] = (entry[0], entry[1], child)
                cur = child
        else:
            child = {_NODE_TAG: True, "k": "obj", "pairs": [], "trailing": [], "index": {}}
            pairs.append((decoded, [], child))
            index[decoded] = len(pairs) - 1
            cur = child
        pairs = cur["pairs"]
        index = cur["index"]

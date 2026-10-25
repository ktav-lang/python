"""Lossless source-value edit: the pure-Python splice engine.

A port of the Rust core's positional-tree splice (``edit::tree`` /
``edit::splice`` / ``edit::splice::layout``) onto the pure-Python
parser's invariants. The document is never parse→mutate→serialize:
only the bytes of the target value (and of inline wrappers the layout
rules force to unfold) are replaced; comments, key spelling, blank
lines, BOM, CR/LF/CRLF, and the presence or absence of the final EOL
all survive. Every successful patch is re-parsed and semantically
verified, so a silent corruption is impossible.

All internal offsets are *character* offsets into the source ``str``
(slicing-safe); the only byte offsets this module hands out are the
``InvalidPath`` ones computed over the path argument itself, which the
contract pins as UTF-8 byte offsets.

This module is the entry point only; the implementation lives in
focused private siblings:

- :mod:`._edit_common` — error helpers, textual-path parsing,
  category-exact value equality, line/EOL context helpers.
- :mod:`._edit_tree` — the positional tree (slots, dotted-key/reopen).
- :mod:`._edit_encode` — replacement-body planning (markers, inline
  encoding, verbatim blocks, pretty compound rendering).
- :mod:`._edit_layout` — minimal inline unfolding.
- :mod:`._edit_splice` — the apply/verify loop and public entry ops.

Import cycle note: the graph is a strict DAG (common ← tree/encode ←
layout ← splice ← this entry), so no circular imports exist.
"""

from __future__ import annotations

from ._edit_common import parse_path
from ._edit_splice import apply_edit, edit_value, edit_value_segments

__all__ = ["apply_edit", "edit_value", "edit_value_segments", "parse_path"]

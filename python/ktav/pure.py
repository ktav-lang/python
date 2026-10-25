"""Explicit pure-Python backend: ``from ktav import pure``.

A full, honest, bidirectional Ktav parser and generator in pure Python
— no Rust extension, WASM, or subprocess is ever loaded. Importing
this module never requires ``ktav._core``.

The API mirrors the native surface exactly; see :mod:`ktav._pure` for
the per-function contracts.

    from ktav import pure

    config = pure.loads(open("config.ktav").read())
    text = pure.dumps({"port": 8080})
    formatted = pure.format(open("config.ktav").read())
"""

from __future__ import annotations

from ._pure import (
    KtavDecodeError,
    KtavEditError,
    KtavEncodeError,
    KtavError,
    KtavInvalidPathError,
    KtavNotFoundError,
    KtavUnsupportedError,
    __spec_version__,
    __version__,
    canonical_from_source,
    dump,
    dumps,
    dumps_force_strings,
    edit_value,
    edit_value_segments,
    emit_canonical,
    format,
    load,
    loads,
    loads_strict,
)

__all__ = [
    "KtavDecodeError",
    "KtavEditError",
    "KtavEncodeError",
    "KtavError",
    "KtavInvalidPathError",
    "KtavNotFoundError",
    "KtavUnsupportedError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dump",
    "dumps",
    "dumps_force_strings",
    "edit_value",
    "edit_value_segments",
    "emit_canonical",
    "format",
    "load",
    "loads",
    "loads_strict",
]

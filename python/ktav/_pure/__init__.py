"""Pure-Python Ktav backend.

A full, dependency-free alternative parser and generator (spec 0.8.1).

No Rust extension, WASM, or subprocess is loaded: everything here is
plain Python. The public surface mirrors the native ``ktav._core``
binding exactly:

- :func:`loads` / :func:`loads_strict` — parse to native values.
- :func:`dumps` / :func:`emit_canonical` / :func:`dumps_force_strings`
  — write from native values.
- :func:`format` — comment-preserving text-to-text formatter.
- :func:`canonical_from_source` — ``emit_canonical(loads(text))``
  without materialising the value tree.
- :data:`__version__` / :data:`__spec_version__` — ``"0.8.1"``.

Errors are the same :class:`KtavError` /
:class:`KtavDecodeError` / :class:`KtavEncodeError` classes with the
same ten structured attributes as the native binding; ``str(exc)`` is
the human-readable message.
"""

from __future__ import annotations

from typing import Any

from ._text import validate_utf8
from .errors import KtavDecodeError, KtavEncodeError, KtavError
from .parser import parse_document
from .writer import (
    canonical_from_source,
    dumps,
    dumps_force_strings,
    emit_canonical,
    format,
)


def _as_str(s: str | bytes | bytearray | memoryview) -> str:
    """Coerce ``s`` to text for the parse entry points.

    Accepts ``str`` or UTF-8 ``bytes``; bytes are validated (§ 6.15)
    before any grammar processing.
    """
    if isinstance(s, (bytes, bytearray, memoryview)):
        return validate_utf8(bytes(s))
    return s


__all__ = [
    "KtavDecodeError",
    "KtavEncodeError",
    "KtavError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dumps",
    "dumps_force_strings",
    "emit_canonical",
    "format",
    "loads",
    "loads_strict",
]

__version__ = "0.8.1"
__spec_version__ = "0.8.1"


def loads(s: str) -> Any:
    """Parse a Ktav document string into a native Python value.

    Mapping (spec 0.8.1): ``null`` → ``None``, ``true``/``false`` →
    ``bool``, integer literal (§ 3.6) → ``int`` (i64 range; overflow →
    ``str``, with decimal→float fallback where applicable), float literal →
    ``float``, bare / ``::`` scalar → ``str``, ``[ … ]`` → ``list``,
    ``{ … }`` → ``dict``. Floats are IEEE 754 binary64 (roundTiesToEven).

    Raises :class:`KtavDecodeError` on malformed input.
    """
    return parse_document(_as_str(s), strict=False)


def loads_strict(s: str) -> Any:
    """Parse a Ktav document with strict canonical-scalar validation.

    In addition to ordinary syntax validation, strict mode rejects
    scalar spellings that would not survive a parse/render round-trip
    unchanged (§ 5.2 LossyScalar, e.g. ``1.10`` → ``1.1``), reporting
    the offending ``body`` and its ``canonical`` form.

    Raises :class:`KtavDecodeError` on malformed input.
    """
    return parse_document(_as_str(s), strict=True)


def load(fp: Any) -> Any:
    """Parse a Ktav document read from a file-like object (text or.

    binary mode).
    """
    return loads(fp.read())


def dump(obj: Any, fp: Any) -> None:
    """Serialize ``obj`` as a Ktav document and write it to ``fp``."""
    text = dumps(obj)
    try:
        fp.write(text)
    except TypeError:
        fp.write(text.encode("utf-8"))

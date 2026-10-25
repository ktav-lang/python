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
- :func:`edit_value` / :func:`edit_value_segments` — lossless
  source-value splice (source-edit 0.9; the version markers below keep
  the released 0.8.1 values until the coordinated version bump).
- :data:`__version__` / :data:`__spec_version__` — ``"0.8.1"``.

Errors are the same :class:`KtavError` /
:class:`KtavDecodeError` / :class:`KtavEncodeError` classes with the
same ten structured attributes as the native binding; ``str(exc)`` is
the human-readable message.
"""

from __future__ import annotations

from typing import Any

from ._text import validate_utf8
from .errors import (
    KtavDecodeError,
    KtavEditError,
    KtavEncodeError,
    KtavError,
    KtavInvalidPathError,
    KtavNotFoundError,
    KtavUnsupportedError,
)
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
    "KtavEditError",
    "KtavEncodeError",
    "KtavError",
    "KtavInvalidPathError",
    "KtavNotFoundError",
    "KtavUnsupportedError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dumps",
    "dumps_force_strings",
    "edit_value",
    "edit_value_segments",
    "emit_canonical",
    "format",
    "loads",
    "loads_strict",
]

__version__ = "0.8.1"
__spec_version__ = "0.8.1"


def loads(s: str) -> Any:
    """Parse a Ktav document string into a native Python value.

    Mapping (spec 0.9): ``null`` → ``None``, ``true``/``false`` →
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


def edit_value(source: str | bytes | bytearray | memoryview, path: str, replacement: Any) -> str:
    r"""Replace the value at the textual ``path`` in ``source``.

    ``path`` is the dotted form (``key1.key2.0.key4``) where ``\\.``
    escapes a literal dot and ``\\\\`` a literal backslash; any other
    escape raises :class:`KtavInvalidPathError` whose ``body`` carries
    the UTF-8 byte offset of the problem. The source must parse; only
    the bytes of the target (and, when the layout rules demand it, of
    inline ancestor wrappers) are replaced — comments, key spelling,
    whitespace, BOM, and CR/LF/CRLF all survive. A replacement equal to
    the current value is a byte-identical no-op.

    ``replacement`` is a native Python value (``None`` / ``bool`` /
    ``int`` / ``float`` / ``str`` / ``list`` / ``dict``). Raises
    :class:`KtavNotFoundError` for a path that addresses nothing,
    :class:`KtavUnsupportedError` when no lossless splice exists, and
    :class:`KtavDecodeError` for a replacement that cannot be encoded.
    """
    from ._edit import parse_path
    from .parser import parse_document

    # Source first: validate + parse BEFORE the path transport decode so
    # a malformed source reports the real 0.9 envelope, not InvalidPath.
    parse_document(_as_str(source))
    return edit_value_segments(_as_str(source), parse_path(path), replacement)


def edit_value_segments(
    source: str | bytes | bytearray | memoryview,
    segments: Any,
    replacement: Any,
) -> str:
    """:func:`edit_value` with already-decoded literal segments.

    ``segments`` is a sequence of exact key strings — no additional
    unescaping. A numeric segment is a string key inside an Object and
    a zero-based ASCII-digits index inside an Array (leading zeros
    allowed, signs are not indexes). An empty sequence raises
    :class:`KtavNotFoundError`.
    """
    from ._edit import apply_edit
    from .parser import parse_document
    from .writer import to_value

    # Source first (see :func:`edit_value`).
    text = _as_str(source)
    parse_document(text)
    decoded = list(segments)
    for segment in decoded:
        if not isinstance(segment, str):
            raise KtavEditError("edit path segments must be strings", error="Message")
    if not decoded:
        # An empty segments list addresses nothing — NotFound, matching
        # the segments API contract (never a noncontiguous Unsupported).
        raise KtavNotFoundError(
            "edit path does not address an existing value", error="EditNotFound"
        )
    return apply_edit(text, decoded, to_value(replacement))


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

"""Ktav — a plain configuration format. Python bindings.

The public entry points mirror the standard library's ``json`` module::

    import ktav

    config = ktav.loads(open("config.ktav").read())
    text = ktav.dumps({"port": 8080, "name": "service"})
    formatted = ktav.format(open("config.ktav").read())  # normalise, keep comments

File-like convenience wrappers live alongside:

    with open("config.ktav") as f:
        config = ktav.load(f)

    with open("config.ktav", "w") as f:
        ktav.dump(config, f)

See https://github.com/ktav-lang/spec for the format specification.
"""

from __future__ import annotations

from typing import IO, Any

from ktav._core import (
    KtavDecodeError,
    KtavEncodeError,
    KtavError,
    __spec_version__,
    __version__,
)
from ktav._core import (
    canonical_from_source as _canonical_from_source,
)
from ktav._core import (
    dumps as _dumps,
)
from ktav._core import (
    dumps_force_strings as _dumps_force_strings,
)
from ktav._core import (
    emit_canonical as _emit_canonical,
)
from ktav._core import (
    format as _format,
)
from ktav._core import (
    loads as _loads,
)
from ktav._core import (
    loads_strict as _loads_strict,
)

__all__ = [
    "KtavDecodeError",
    "KtavEncodeError",
    "KtavError",
    "__spec_version__",
    "__version__",
    "canonical_from_source",
    "dump",
    "dumps",
    "dumps_force_strings",
    "emit_canonical",
    "format",
    "load",
    "loads",
    "loads_strict",
]


def loads(s: str | bytes | bytearray) -> Any:
    """Parse a Ktav document from a string (or UTF-8 bytes)."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8")
    return _loads(s)


def loads_strict(s: str | bytes | bytearray) -> Any:
    """Parse a Ktav document with strict canonical-scalar validation."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8")
    return _loads_strict(s)


def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string.

    The top-level value must be a mapping (``dict``) or a sequence
    (``list`` / ``tuple``). Top-level Arrays render as bare
    item-per-line — no surrounding ``[...]`` brackets (spec § 5.0.1,
    added in 0.1.1). Raises :class:`KtavEncodeError` otherwise.
    """
    return _dumps(obj)


def emit_canonical(obj: Any) -> str:
    """Emit the canonical (normalised) form of ``obj`` as a Ktav document.

    The output is byte-deterministic across all compliant implementations
    (spec § 5.9): numbers are normalised, redundant whitespace stripped,
    and inline forms expanded to multi-line. The top-level value must be
    a mapping (``dict``) or a sequence (``list`` / ``tuple``). Raises
    :class:`KtavEncodeError` otherwise.
    """
    return _emit_canonical(obj)


def format(s: str | bytes | bytearray) -> str:
    """Format a Ktav document: text in, normalised text out.

    Normalises the document's structure to the canonical shape
    (spec § 5.9) while preserving every comment line and blank-line
    grouping. Comments survive verbatim (spec § 3.4: a comment owns a
    whole line); a run of two or more blank lines collapses to exactly
    one and blank padding immediately inside a bracket is dropped, so
    formatting is a fixed point: ``format(format(x)) == format(x)``.
    Key order is never changed (canonical form has no sorting rule).

    For a document with no comments and no blank lines the result
    equals :func:`emit_canonical` of its parse.

    Raises :class:`KtavDecodeError` on malformed input.
    """
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8")
    return _format(s)


def canonical_from_source(s: str | bytes | bytearray) -> str:
    """Re-emit a Ktav document in canonical form: text in, text out.

    The result equals ``emit_canonical(loads(s))``, but the document
    never becomes a Python object on the way, so spec § 5.9 stays
    decided in the one layer that owns it.

    Unlike :func:`format`, comments and blank lines do NOT survive —
    canonical form carries no trivia. Use :func:`format` to tidy a file
    a human will read, and this to produce a byte-stable form to hash,
    diff or store.

    Raises :class:`KtavDecodeError` on malformed input.
    """
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8")
    return _canonical_from_source(s)


def dumps_force_strings(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document with every scalar coerced to a String.

    Typed integers, typed floats, booleans, and ``None`` are flattened
    to their textual form and emitted via the raw ``::`` marker so the
    output round-trips back through the parser as the same string
    scalars. Compounds (``dict`` / ``list`` / ``tuple``) preserve their
    structure; only leaf scalars are coerced.

    Useful for "everything is a string" downstream consumers — e.g.
    environment variables, or diffs where the textual form is the
    canonical source of truth.

    Raises :class:`KtavEncodeError` on unsupported types or
    unrepresentable values.
    """
    return _dumps_force_strings(obj)


def load(fp: IO[Any]) -> Any:
    """Parse a Ktav document read from a file-like object.

    Accepts both text-mode (``str``) and binary-mode (``bytes``) files.
    """
    return loads(fp.read())


def dump(obj: Any, fp: IO[Any]) -> None:
    """Serialize ``obj`` as a Ktav document and write it to ``fp``.

    Accepts both text-mode and binary-mode files. Binary mode writes
    UTF-8 bytes.
    """
    text = dumps(obj)
    try:
        fp.write(text)
    except TypeError:
        fp.write(text.encode("utf-8"))

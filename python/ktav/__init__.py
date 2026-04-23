"""Ktav — a plain configuration format. Python bindings.

The public entry points mirror the standard library's ``json`` module::

    import ktav

    config = ktav.loads(open("config.ktav").read())
    text = ktav.dumps({"port": 8080, "name": "service"})

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
    dumps as _dumps,
)
from ktav._core import (
    loads as _loads,
)

__all__ = [
    "KtavDecodeError",
    "KtavEncodeError",
    "KtavError",
    "__spec_version__",
    "__version__",
    "dump",
    "dumps",
    "load",
    "loads",
]


def loads(s: str | bytes | bytearray) -> Any:
    """Parse a Ktav document from a string (or UTF-8 bytes)."""
    if isinstance(s, (bytes, bytearray)):
        s = bytes(s).decode("utf-8")
    return _loads(s)


def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string.

    The top-level value must be a mapping (``dict``) — Ktav documents are
    objects. Raises :class:`KtavEncodeError` otherwise.
    """
    return _dumps(obj)


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

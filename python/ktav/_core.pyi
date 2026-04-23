"""Type stubs for the ``ktav._core`` compiled extension.

The bindings are implemented in Rust via PyO3 (see ``src/lib.rs``). This
file is the source of truth for type-checkers — mypy, pyright, IDEs —
since the .so / .pyd does not carry Python-level annotations.
"""

from typing import Any

__version__: str
__spec_version__: str

def loads(s: str) -> Any:
    """Parse a Ktav document string into a native Python value.

    Mapping:

    ======================  ==============
    Ktav                    Python
    ======================  ==============
    ``null``                ``None``
    ``true`` / ``false``    ``bool``
    ``:i <digits>``         ``int``
    ``:f <number>``         ``float``
    bare scalar             ``str``
    ``[ ... ]``             ``list``
    ``{ ... }``             ``dict``
    ======================  ==============

    Raises :class:`KtavDecodeError` on malformed input.
    """

def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string.

    The top-level value must be a ``dict``. Supported value types:
    ``None``, ``bool``, ``int``, ``float``, ``str``, ``list``, ``tuple``,
    ``dict``. ``NaN`` and ``±Infinity`` are rejected — Ktav 0.1.0 does
    not represent them.

    Raises :class:`KtavEncodeError` on unsupported types or
    unrepresentable values.
    """

class KtavError(Exception):
    """Base class for every exception raised by this library."""

class KtavDecodeError(KtavError):
    """Raised when parsing a Ktav document fails."""

class KtavEncodeError(KtavError):
    """Raised when serialising a Python value to Ktav fails."""

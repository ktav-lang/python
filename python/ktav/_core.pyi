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

    Mapping (spec 0.5.0):

    ==============================  ==============
    Ktav                            Python
    ==============================  ==============
    ``null``                        ``None``
    ``true`` / ``false``            ``bool``
    integer literal (§ 3.6)        ``int``
    float literal (§ 3.6)          ``float``
    bare / ``::`` scalar            ``str``
    ``[ ... ]`` / ``[i, …]``        ``list``
    ``{ ... }`` / ``{k: v, …}``     ``dict``
    ==============================  ==============

    Raises :class:`KtavDecodeError` on malformed input.
    """

def loads_strict(s: str) -> Any:
    """Parse a Ktav document with strict canonical-scalar validation.

    In addition to ordinary syntax validation, strict mode rejects scalar
    spellings that would not survive a parse/render round-trip unchanged.
    """

def dumps(obj: Any) -> str:
    """Serialize ``obj`` as a Ktav document string.

    The top-level value must be a ``dict`` or a sequence (``list`` /
    ``tuple``); top-level Arrays render as bare item-per-line (spec
    § 5.0.1, added 0.1.1). Supported value types: ``None``, ``bool``,
    ``int``, ``float``, ``str``, ``list``, ``tuple``, ``dict``. ``NaN``
    and ``±Infinity`` are rejected — Ktav does not represent them.

    Raises :class:`KtavEncodeError` on unsupported types or
    unrepresentable values.
    """

def emit_canonical(obj: Any) -> str:
    """Emit the canonical (normalised) form of ``obj`` as a Ktav document.

    The output is byte-deterministic across all compliant implementations
    (spec § 5.9). The top-level value must be a ``dict`` or a sequence
    (``list`` / ``tuple``). Raises :class:`KtavEncodeError` otherwise.
    """

def dumps_force_strings(obj: Any) -> str:
    """Serialize ``obj`` with every scalar coerced to a String.

    Typed integers, typed floats, booleans, and ``None`` are flattened
    to their textual form and emitted via the raw ``::`` marker so the
    output round-trips back through the parser as the same string
    scalars. Compounds preserve their structure; only leaf scalars are
    coerced. Same top-level constraints as :func:`dumps`.

    Raises :class:`KtavEncodeError` on unsupported types or
    unrepresentable values.
    """

class KtavError(Exception):
    """Base class for every exception raised by this library."""

class KtavDecodeError(KtavError):
    """Raised when parsing a Ktav document fails."""

class KtavEncodeError(KtavError):
    """Raised when serialising a Python value to Ktav fails."""

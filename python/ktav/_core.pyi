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

def canonical_from_source(s: str) -> str:
    """Parse ``s`` and emit its canonical (normalised) form directly.

    Equivalent to ``emit_canonical(loads(s))`` but never builds a
    Python object on the way — spec § 5.9 stays decided in the Rust
    layer that owns it. Raises :class:`KtavDecodeError` on malformed
    input.
    """

def format(s: str) -> str:
    """Format a Ktav document: text in, normalised text out.

    Normalises structure to canonical form (spec § 5.9) while
    preserving every comment and blank-line grouping; a fixed point
    (``format(format(x)) == format(x)``). Key order is never changed.
    For a document with no comments and no blank lines the result
    equals ``emit_canonical`` of its parse.

    Raises :class:`KtavDecodeError` on malformed input.
    """

class KtavError(Exception):
    """Base class for every exception raised by this library.

    Since 0.7.1 every raised instance carries the structured error
    envelope (ktav issue rust#12) as attributes. ``str(exc)`` stays a
    human-readable message, never the raw envelope.

    - ``error``: envelope class name — the parser's error kind (e.g.
      ``"LossyScalar"``, ``"DuplicateKey"``), ``"Unrepresentable"`` /
      ``"UnrepresentableAt"`` for writer rejections, or ``"Message"``.
    - ``reason``: writer-time § 5.9.0 reason code (e.g.
      ``"NonFiniteFloat"``, ``"ScalarRoot"``); ``None`` otherwise.
    - ``line``: 1-based source line, parse-time only.
    - ``line_text``: the offending source line, parse-time only.
    - ``span``: ``{"start": int, "end": int}`` — byte offsets into the
      UTF-8 source — parse-time only.
    - ``path``: list of exact decoded key segments (a key literally
      named ``a.b`` is ONE segment, never split), or ``None``.
    - ``body``: class-specific payload (e.g. ``LossyScalar``'s source
      form) or ``None``.
    - ``canonical``: canonical spelling where one exists (``LossyScalar``).
    - ``spec_section``: governing spec section (e.g. ``"§6.2"``).
    """

    error: str
    reason: str | None
    line: int | None
    line_text: str | None
    span: dict[str, int] | None
    path: list[str] | None
    body: str | None
    canonical: str | None
    spec_section: str | None

class KtavDecodeError(KtavError):
    """Raised when parsing a Ktav document fails."""

class KtavEncodeError(KtavError):
    """Raised when serialising a Python value to Ktav fails."""

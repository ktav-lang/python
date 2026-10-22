"""Structured error envelope for the pure-Python backend.

Mirrors the Rust core's ten-field envelope (ktav issue rust#12) and the
PyO3 binding's exception attributes exactly: every raised instance
carries all ten attributes, ``None`` where absent, and ``str(exc)`` is
the human-readable message — never the envelope.
"""

from __future__ import annotations

from typing import Any, NoReturn

__all__ = [
    "KtavDecodeError",
    "KtavEncodeError",
    "KtavError",
]


class KtavError(Exception):
    """Base class for every exception raised by this library.

    Every instance carries the ten-field structured error envelope as
    attributes: ``error``, ``reason``, ``line``, ``line_text``, ``span``,
    ``path``, ``body``, ``canonical``, ``spec_section``, ``message``.
    ``str(exc)`` stays a human-readable message, never the envelope.
    """

    error: str
    reason: str | None
    line: int | None
    line_text: str | None
    span: dict[Any, Any] | None
    path: list[Any] | None
    body: str | None
    canonical: str | None
    spec_section: str | None
    message: str

    def __init__(
        self,
        message: str,
        *,
        error: str = "Message",
        reason: str | None = None,
        line: int | None = None,
        line_text: str | None = None,
        span: dict[Any, Any] | None = None,
        path: list[Any] | None = None,
        body: str | None = None,
        canonical: str | None = None,
        spec_section: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.reason = reason
        self.line = line
        self.line_text = line_text
        self.span = span
        self.path = path
        self.body = body
        self.canonical = canonical
        self.spec_section = spec_section
        self.message = message


class KtavDecodeError(KtavError):
    """Raised when parsing a Ktav document fails."""


class KtavEncodeError(KtavError):
    """Raised when serialising a Python value to Ktav fails."""


# ---------------------------------------------------------------------------
# Display strings — verbatim mirrors of the Rust core's `Display` impls,
# so ``str(exc)`` (and ``exc.message``) is byte-identical across
# backends.
# ---------------------------------------------------------------------------

REASON_DISPLAY = {
    "ScalarRoot": ("ScalarRoot: the document root is not an Object or an Array (spec § 5.9.0)"),
    "EmptyKeyName": ("EmptyKeyName: an Object pair's name is the empty string (spec § 5.9.0)"),
    "NonFiniteFloat": ("NonFiniteFloat: a Float is NaN or ±Infinity (spec § 5.9.0)"),
    "CRByte": ("CRByte: a String contains a CR byte (spec § 5.9.0 / § 5.9.7)"),
    "BothFormsRequired": (
        "BothFormsRequired: the multi-line String needs both forms, a segment"
        " trimming to '))' and a segment trimming to ')' (spec § 5.9.7)"
    ),
    "TrailingWhitespaceCollision": (
        "TrailingWhitespaceCollision: a segment trims to '))' and some content"
        " line has trailing whitespace (spec § 5.9.7)"
    ),
    "LeadingWhitespaceCollision": (
        "LeadingWhitespaceCollision: a segment trims to '))' and every"
        " non-blank segment shares leading whitespace at the same position"
        " (spec § 5.9.7)"
    ),
}

#: Governing spec section per parse-time category (mirrors the Rust
#: envelope's ``kind_spec_section``).
SPEC_SECTIONS = {
    "InvalidUtf8": "§6.15",
    "MissingSeparatorSpace": "§6.10",
    "LossyScalar": "§3.6/§5.2",
    "DuplicateKey": "§6.2",
    "KeyPathConflict": "§6.3",
    "EmptyKey": "§6.5",
    "InvalidKey": "§6.4",
    "UnclosedCompound": "§6.1",
    "UnbalancedBracket": "§6.1",
    "MissingSeparator": "§6.6",
    "UnterminatedInlineCompound": "§6.11",
    "UnterminatedQuotedKey": "§6.16",
    "MalformedInlineCompound": "§6.12",
    "BadEscapeSequence": "§6.13",
    "OrphanLineAfterTopLevelInline": "§6.14",
}

REASON_SPEC_SECTIONS = {
    "ScalarRoot": "§5.9.0",
    "EmptyKeyName": "§5.9.0",
    "NonFiniteFloat": "§5.9.0",
    "CRByte": "§5.9.7",
    "BothFormsRequired": "§5.9.7",
    "TrailingWhitespaceCollision": "§5.9.7",
    "LeadingWhitespaceCollision": "§5.9.7",
}


def raise_decode(
    category: str,
    line: int | None,
    line_text: str | None,
    span: dict[Any, Any],
    message: str,
    *,
    path: list[Any] | None = None,
    body: str | None = None,
    canonical: str | None = None,
) -> NoReturn:
    """Build and raise a :class:`KtavDecodeError` with a full envelope."""
    raise KtavDecodeError(
        message,
        error=category,
        line=line,
        line_text=line_text,
        span=span,
        path=path,
        body=body,
        canonical=canonical,
        spec_section=SPEC_SECTIONS.get(category),
    )


def raise_encode_reason(reason: str, path: list[Any] | None = None) -> NoReturn:
    """Raise a writer-time § 5.9.0 rejection, optionally path-carrying."""
    if path is None:
        raise KtavEncodeError(
            REASON_DISPLAY[reason],
            error="Unrepresentable",
            reason=reason,
            spec_section=REASON_SPEC_SECTIONS[reason],
        )
    raise KtavEncodeError(
        REASON_DISPLAY[reason],
        error="UnrepresentableAt",
        reason=reason,
        path=path,
        spec_section=REASON_SPEC_SECTIONS[reason],
    )

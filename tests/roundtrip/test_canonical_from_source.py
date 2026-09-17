"""`canonical_from_source` — text in, canonical text out, in one call.

Pinned against the via-a-value route so the two cannot drift apart, and
against the § 5.9.8 threshold that decides fixed vs scientific float
form.
"""

import ktav
import pytest


def test_matches_emit_canonical_of_the_parse() -> None:
    src = "zebra: 1.10\napple: 1.0e3\nbig: 1e9\n"
    assert ktav.canonical_from_source(src) == ktav.emit_canonical(ktav.loads(src))


def test_normalises_float_spelling_per_section_5_9_8() -> None:
    # Fixed form below 1e7, scientific at or above it.
    assert ktav.canonical_from_source("v: 1.10\n") == "v: 1.1\n"
    assert ktav.canonical_from_source("v: 1.0e3\n") == "v: 1000.0\n"
    assert ktav.canonical_from_source("v: 1e9\n") == "v: 1e9\n"


def test_preserves_source_key_order() -> None:
    out = ktav.canonical_from_source("zebra: 1\napple: 2\n")
    assert out.index("zebra") < out.index("apple")


def test_drops_the_trivia_that_format_keeps() -> None:
    src = "## a comment\nport: 8080\n"
    assert "## a comment" in ktav.format(src)
    assert "## a comment" not in ktav.canonical_from_source(src)


def test_accepts_utf8_bytes_like_the_other_readers() -> None:
    assert ktav.canonical_from_source(b"v: 1.10\n") == "v: 1.1\n"
    assert ktav.canonical_from_source(bytearray(b"v: 1.10\n")) == "v: 1.1\n"


def test_rejects_malformed_source_with_the_envelope() -> None:
    with pytest.raises(ktav.KtavDecodeError) as exc_info:
        ktav.canonical_from_source("a: [")
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert isinstance(e.message, str)
    assert e.message != ""

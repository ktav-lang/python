"""The comment-preserving formatter (`ktav.format`, ktav 0.7.1)."""

import ktav
import pytest

SOURCE = """\
## service configuration
name: my-service

port: 8080
## listen on all interfaces
host: 0.0.0.0


tags: [a, b]
"""


def test_comments_are_preserved_verbatim() -> None:
    formatted = ktav.format(SOURCE)
    assert "## service configuration" in formatted
    assert "## listen on all interfaces" in formatted


def test_format_is_a_fixed_point() -> None:
    once = ktav.format(SOURCE)
    assert ktav.format(once) == once


def test_blank_runs_collapse_to_one() -> None:
    assert "\n\n\n" not in ktav.format(SOURCE)


def test_value_is_preserved() -> None:
    assert ktav.loads(ktav.format(SOURCE)) == ktav.loads(SOURCE)


def test_no_comments_no_blanks_equals_emit_canonical_of_parse() -> None:
    text = "name: svc\nport: 8080\ninline: {a: 1}\n"
    assert ktav.format(text) == ktav.emit_canonical(ktav.loads(text))


def test_key_order_is_unchanged() -> None:
    formatted = ktav.format(SOURCE)
    assert formatted.index("port: 8080") < formatted.index("host: 0.0.0.0")
    assert formatted.index("host: 0.0.0.0") < formatted.index("tags:")


def test_bytes_input_accepted() -> None:
    assert ktav.format(b"a: 1\n") == ktav.format("a: 1\n")


def test_invalid_utf8_bytes_raise_unicodedecodeerror() -> None:
    with pytest.raises(UnicodeDecodeError):
        ktav.format(b"\xff\xfe: 1\n")


def test_malformed_input_raises_decode_error() -> None:
    with pytest.raises(ktav.KtavDecodeError):
        ktav.format("x: [")


def test_document_leading_and_trailing_blank_lines_are_dropped() -> None:
    assert ktav.format("\n\na: 1\n\n\n") == "a: 1\n"


def test_empty_and_comment_only_documents() -> None:
    assert ktav.format("") == ""
    comment_only = ktav.format("## only a comment\n")
    assert "## only a comment" in comment_only

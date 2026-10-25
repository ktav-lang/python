"""Public root-API `edit_value_segments` contract (both backends).

Covers the Python-level wrapper semantics that the pure and native
entry ops do not see themselves:

- source-first: a broken source wins over a bad segments transport;
- non-string segments on a VALID source are the active backend's
  typed Message error with all-null positions;
- generator segments are materialized once (never drained twice).
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()

FIELDS = (
    "error",
    "reason",
    "line",
    "line_text",
    "span",
    "path",
    "body",
    "canonical",
    "spec_section",
    "message",
)


@pytest.mark.parametrize("api", APIS)
def test_valid_source_nonstr_segments_are_a_typed_message(api: Any) -> None:
    segments: Any = ["a", 0]
    with pytest.raises(api.KtavEditError) as exc_info:
        api.edit_value_segments("a: 1\n", segments, 2)
    e = exc_info.value
    for field in FIELDS:
        assert hasattr(e, field)
    assert e.error == "Message"
    assert e.message == "edit path segments must be strings"
    assert str(e) == e.message
    # A transport error never invents source positions.
    assert e.reason is None
    assert e.line is None
    assert e.line_text is None
    assert e.span is None
    assert e.path is None
    assert e.body is None
    assert e.canonical is None
    assert e.spec_section is None
    # Identity: raised under the ACTIVE backend's class.
    assert isinstance(e, api.KtavEditError)


@pytest.mark.parametrize("api", APIS)
def test_broken_source_beats_nonstr_segments(api: Any) -> None:
    segments: Any = ["a", 0]
    with pytest.raises(api.KtavDecodeError) as exc_info:
        api.edit_value_segments("a: {", segments, 2)
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert e.line == 1
    assert e.span is not None
    assert e.span["end"] > e.span["start"]


@pytest.mark.parametrize("api", APIS)
def test_generator_segments_are_materialized_once(api: Any) -> None:
    gen = iter(["a", "0"])
    out = api.edit_value_segments("a: [old]\n", gen, "new")
    assert out == "a: [new]\n"
    # The generator was consumed exactly once by the wrapper.
    assert list(gen) == []

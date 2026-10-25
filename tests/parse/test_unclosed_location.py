"""UnclosedCompound span start must be the REAL opener byte (0.9).

Regression for the diagnostics09 `eof_nested` / `eof_*` class: the span
starts at the innermost opener (`{` / `[` / `(` / `((`), after any
indent and after the `key:` separator — never at the pair/line start.
"""

from __future__ import annotations

from typing import Any

import pytest

import ktav
import ktav.pure as pure


def _apis() -> list[Any]:
    """pure always; native only when its symbols really exist.

    In the explicitly pure-mode CI job the compiled extension is absent
    by construction, so only the pure backend is parametrized there.
    """
    apis: list[Any] = [pure]
    native_loads = getattr(ktav, "_loads", None)
    if (
        ktav._HAS_CORE
        and native_loads is not None
        and not getattr(native_loads, "_ktav_stub", False)
    ):
        apis.insert(0, ktav)
    return apis


APIS = _apis()


@pytest.mark.parametrize("api", APIS)
def test_nested_block_opener_offset(api: Any) -> None:
    source = "a: {\n  b: {\n"
    with pytest.raises(api.KtavDecodeError) as exc_info:
        api.loads(source)
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert e.line == 2, e.line
    assert e.line_text == "  b: {"
    assert e.span is not None
    assert e.span["start"] == 10, e.span  # the inner '{', after '  b: '
    assert e.span["end"] == len(source.encode("utf-8"))


@pytest.mark.parametrize("api", APIS)
def test_multiline_opener_offset(api: Any) -> None:
    source = "k: (\n hi\n"
    with pytest.raises(api.KtavDecodeError) as exc_info:
        api.loads(source)
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert e.line == 1
    assert e.span is not None
    assert e.span["start"] == 3, e.span  # the '(', right after 'k: '


@pytest.mark.parametrize("api", APIS)
def test_explicit_root_opener_offset_with_indent(api: Any) -> None:
    source = "  {\n"
    with pytest.raises(api.KtavDecodeError) as exc_info:
        api.loads(source)
    e = exc_info.value
    assert e.error == "UnclosedCompound"
    assert e.span is not None
    assert e.span["start"] == 2, e.span

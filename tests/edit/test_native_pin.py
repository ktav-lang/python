"""Pin guard: a native extension MUST expose the source-edit 0.9 symbols.

The edit regression suites quietly restrict themselves to the pure
backend when the extension lacks the edit symbols (pre-pin bootstrap).
After the parent's immutable core pin that degradation would silently
halve coverage, so this guard fails loudly instead: whenever the
compiled extension is importable at all, its edit symbols must be real
— never the loud-stub fallback — and must actually work.

Skipped ONLY in the pure-mode CI job, where ``ktav._core`` is absent
by construction (conftest enforces that scenario separately).
"""

from __future__ import annotations

import pytest

import ktav


@pytest.mark.skipif(not ktav._HAS_CORE, reason="pure-mode job: extension absent")
def test_native_edit_symbols_are_real_after_the_pin() -> None:
    for name in ("_edit_value", "_edit_value_segments"):
        fn = getattr(ktav, name, None)
        assert fn is not None, f"ktav.{name} missing from the module surface"
        assert not getattr(fn, "_ktav_stub", False), (
            f"ktav._core does not export the source-edit 0.9 symbol behind"
            f" ktav.{name}; the Cargo core pin (immutable rev) has drifted"
            " — the edit coverage would silently run pure-only"
        )


@pytest.mark.skipif(not ktav._HAS_CORE, reason="pure-mode job: extension absent")
def test_native_edit_works_and_reports_source_errors() -> None:
    if getattr(getattr(ktav, "_edit_value", None), "_ktav_stub", False):
        pytest.fail(
            "native edit symbols are stubs; see test_native_edit_symbols_are_real_after_the_pin"
        )
    assert ktav.edit_value("a: 1\n", "a", 2) == "a: 2\n"
    assert ktav.edit_value_segments("a: [x]\n", ["a", "0"], "y") == "a: [y]\n"
    # 0.9 source-first priority: a malformed source raises the real
    # parser envelope, never a coordinate-less edit error.
    with pytest.raises(ktav.KtavDecodeError) as exc_info:
        ktav.edit_value("a: {", "a", 2)
    assert exc_info.value.error == "UnclosedCompound"
    assert exc_info.value.line is not None

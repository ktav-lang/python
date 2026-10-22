"""CI scenario guards.

Advertised backend scenarios must not silently degrade:

- ``KTAV_REQUIRE_PURE=1`` (the pure-mode CI job): the process must NOT
  have the compiled ``ktav._core`` extension. If anything accidentally
  pulls the native module in, the job fails here instead of quietly
  testing the native path.
- ``KTAV_REQUIRE_NATIVE=1`` (the regular ``test`` job, which builds the
  extension with maturin first): the extension must be present, so a
  silent build regression fails loudly instead of halving coverage.

Missing corpus is NOT guarded here — that is the conformance runner's
fail-closed inventory test: a missing spec submodule is a hard
pytest.fail, never a skip (a skipped suite is indistinguishable from a
green one).
"""

from __future__ import annotations

import os

import ktav


def pytest_configure(config: object) -> None:
    require_pure = os.environ.get("KTAV_REQUIRE_PURE") == "1"
    require_native = os.environ.get("KTAV_REQUIRE_NATIVE") == "1"
    has_core = bool(getattr(ktav, "_HAS_CORE", False))
    if require_pure:
        assert not has_core, (
            "pure-mode scenario violated: ktav._core is importable; the pure-mode"
            " job must run with the compiled extension guaranteed absent"
        )
        assert not hasattr(ktav, "_core"), "native extension leaked into pure mode"
    if require_native:
        assert has_core, (
            "native scenario violated: maturin built nothing importable;"
            " ktav._core is required in the regular test job"
        )

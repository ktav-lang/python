"""Edit-backend parametrization: pure always, native when importable.

Native and pure MUST agree byte-for-byte on every edit regression, so
both participate in the same oracle-driven cases whenever the compiled
extension exposes the source-edit 0.9 symbols. The restriction to the
pure backend is legitimate ONLY in the explicitly pure-mode CI job
(``KTAV_REQUIRE_PURE=1``, extension absent by construction); in a
native job (``KTAV_REQUIRE_NATIVE=1``) a missing/stubbed symbol is a
loud failure here, never a silent skip.
"""

from __future__ import annotations

import os
from typing import Any

import ktav
import ktav.pure


def edit_apis() -> list[Any]:
    apis: list[Any] = [ktav.pure]
    native_edit = getattr(ktav, "_edit_value", None)
    if ktav._HAS_CORE and native_edit is not None and not getattr(native_edit, "_ktav_stub", False):
        apis.insert(0, ktav)
    if os.environ.get("KTAV_REQUIRE_NATIVE") == "1" and len(apis) == 1:
        raise RuntimeError(
            "KTAV_REQUIRE_NATIVE job: the compiled extension does not expose"
            " the source-edit 0.9 edit symbols; native edit coverage would"
            " be silently skipped (see tests/edit/test_native_pin.py)"
        )
    return apis

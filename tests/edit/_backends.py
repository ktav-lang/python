"""Edit-backend parametrization: pure always, native when importable.

Native and pure MUST agree byte-for-byte on every edit regression, so
both participate in the same oracle-driven cases whenever the compiled
extension exposes the source-edit 0.9 symbols.
"""

from __future__ import annotations

from typing import Any

import ktav
import ktav.pure


def edit_apis() -> list[Any]:
    apis: list[Any] = [ktav.pure]
    native_edit = getattr(ktav, "_edit_value", None)
    if ktav._HAS_CORE and native_edit is not None and not getattr(native_edit, "_ktav_stub", False):
        apis.insert(0, ktav)
    return apis

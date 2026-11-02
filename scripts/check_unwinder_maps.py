"""Проверить входные объекты GNU линкера."""

from __future__ import annotations

import re
import sys
from pathlib import Path

GCC_MEMBER = re.compile(r"libgcc(?:_eh|_s)?\.a\([^()\n]+\)")
GCC_CRT = re.compile(r"(?:^|/)crt(?:begin|end)[^/\s]*\.o(?:\s|$)")


def _check(text: str) -> None:
    lines = text.splitlines()
    loads = [line[5:] for line in lines if line.startswith("LOAD ")]
    if not loads or "libunwind.a(" not in text:
        raise ValueError("missing GNU link map inputs or LLVM unwinder members")
    offending = [line for line in lines if GCC_MEMBER.search(line)]
    offending.extend(path for path in loads if GCC_CRT.search(path))
    if offending:
        raise ValueError("GCC runtime input linked: " + "; ".join(dict.fromkeys(offending)))


def main() -> None:
    """Отклонить GCC runtime в каждой сохранённой карте линковки."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_unwinder_maps.py MAP_DIRECTORY")
    try:
        maps = sorted(Path(sys.argv[1]).glob("link.*"))
        if len(maps) < 2:
            raise ValueError("missing wheel or panic probe link map")
        for path in maps:
            _check(path.read_text(encoding="utf-8"))
            print(f"LLVM unwinder link inputs verified: {path.name}")
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

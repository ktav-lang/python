"""Отклонить непроверенные macOS dylibs и iconv/charset imports."""

from __future__ import annotations

import re


def verify(imports: str, undefined_symbols: str) -> None:
    """Проверить only-libSystem и отсутствие iconv/charset imports."""
    lines = imports.splitlines()
    if not lines or not lines[0].endswith(":"):
        raise ValueError("missing macOS library report")
    libraries = []
    for line in lines[1:]:
        match = re.fullmatch(
            r"\s+(\S+) \(compatibility version [0-9.]+, current version [0-9.]+\)",
            line,
        )
        if not match:
            raise ValueError("unrecognized macOS library report")
        libraries.append(match.group(1))
    if libraries != ["/usr/lib/libSystem.B.dylib"]:
        raise ValueError("unreviewed macOS native dependency")
    if not undefined_symbols.strip():
        raise ValueError("missing macOS undefined-symbol report")
    if re.search(r"iconv|charset", undefined_symbols, re.IGNORECASE):
        raise ValueError("unexpected macOS iconv/charset import")

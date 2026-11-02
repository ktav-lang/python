"""Отклонить непроверенные macOS dylibs и iconv/charset imports."""

from __future__ import annotations

import re


def verify(imports: str, undefined_symbols: str, install_name_report: str) -> None:
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
    identity = install_name_report.splitlines()
    if len(identity) != 2 or not identity[0].endswith(":") or not identity[1].strip():
        raise ValueError("missing macOS install-name report")
    if libraries[:1] != [identity[1].strip()]:
        raise ValueError("unreviewed macOS native dependency: missing or misplaced install name")
    dependencies = libraries[1:]
    if dependencies != ["/usr/lib/libSystem.B.dylib"]:
        raise ValueError(f"unreviewed macOS native dependency: {dependencies!r}")
    if not undefined_symbols.strip():
        raise ValueError("missing macOS undefined-symbol report")
    if re.search(r"iconv|charset", undefined_symbols, re.IGNORECASE):
        raise ValueError("unexpected macOS iconv/charset import")

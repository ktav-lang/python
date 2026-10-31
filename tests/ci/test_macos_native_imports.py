"""Проверить fail-closed macOS dependencies без native исполнения."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "macos_native_imports.py"
SPEC = importlib.util.spec_from_file_location("macos_native_imports", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SYSTEM = "\t/usr/lib/libSystem.B.dylib (compatibility version 1.0.0, current version 1351.0.0)\n"
SELF = "\t@rpath/module.so (compatibility version 0.0.0, current version 0.0.0)\n"
REPORT = "module.so:\n" + SELF + SYSTEM
IDENTITY = "module.so:\n@rpath/module.so\n"
SYMBOLS = "_PyLong_FromLong\n_malloc\n"


def test_only_system_library_and_python_symbols_pass() -> None:
    MODULE.verify(REPORT, SYMBOLS, IDENTITY)


@pytest.mark.parametrize(
    "library",
    ["/usr/lib/libiconv.2.dylib", "@rpath/foreign.dylib", "/usr/local/lib/libcharset.dylib"],
)
def test_rejects_extra_libraries(library: str) -> None:
    imports = REPORT + f"\t{library} (compatibility version 1.0.0, current version 1.0.0)\n"
    with pytest.raises(ValueError, match="unreviewed macOS native dependency"):
        MODULE.verify(imports, SYMBOLS, IDENTITY)


@pytest.mark.parametrize(
    "symbol", ["_iconv", "_iconv_open", "_libiconv", "_locale_charset", "_ICONV_close"]
)
def test_rejects_iconv_charset_symbols(symbol: str) -> None:
    with pytest.raises(ValueError, match="iconv/charset import"):
        MODULE.verify(REPORT, SYMBOLS + symbol + "\n", IDENTITY)


@pytest.mark.parametrize("imports", ["", "not a report\n", "module.so:\nmalformed\n"])
def test_rejects_malformed_reports(imports: str) -> None:
    with pytest.raises(ValueError, match="macOS library report"):
        MODULE.verify(imports, SYMBOLS, IDENTITY)


@pytest.mark.parametrize(
    "imports", ["module.so:\n" + SELF, "module.so:\n" + SELF + SYSTEM + SYSTEM]
)
def test_rejects_missing_or_duplicate_system_library(imports: str) -> None:
    with pytest.raises(ValueError, match="unreviewed macOS native dependency"):
        MODULE.verify(imports, SYMBOLS, IDENTITY)


def test_rejects_missing_symbol_evidence() -> None:
    with pytest.raises(ValueError, match="missing macOS undefined-symbol report"):
        MODULE.verify(REPORT, "", IDENTITY)


@pytest.mark.parametrize("identity", ["", "module.so:\n", "module.so:\nfirst\nsecond\n"])
def test_rejects_missing_or_ambiguous_install_name(identity: str) -> None:
    with pytest.raises(ValueError, match="missing macOS install-name report"):
        MODULE.verify(REPORT, SYMBOLS, identity)


def test_rejects_mismatched_install_name() -> None:
    with pytest.raises(ValueError, match="missing or misplaced install name"):
        MODULE.verify(REPORT, SYMBOLS, "module.so:\n@rpath/foreign.so\n")


def test_duplicate_self_reference_is_not_ignored() -> None:
    with pytest.raises(ValueError, match="unreviewed macOS native dependency"):
        MODULE.verify("module.so:\n" + SELF + SELF + SYSTEM, SYMBOLS, IDENTITY)

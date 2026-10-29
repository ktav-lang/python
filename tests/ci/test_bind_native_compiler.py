"""Проверить соответствие compiler source и std evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bind_native_compiler.py"
spec = importlib.util.spec_from_file_location("bind_native_compiler", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
COMPILER = (
    "rustc 1.99.1\nhost: x86_64-unknown-linux-gnu\nrelease: 1.99.1\n"
    f"commit-hash: {'a' * 40}\nLLVM version: 22.1.0\n"
)


def _bundle() -> dict:
    return {
        "schema_version": 1,
        "rustc": COMPILER,
        "rust_standard_library": {"text": "copyright", "sha256": "fixture"},
        "licenses": ["license text"],
    }


def test_records_actual_host_without_replacing_std_source() -> None:
    actual = COMPILER.replace("x86_64", "aarch64")
    result = json.loads(module._bind(_bundle(), actual))
    assert result["rustc"] == actual
    assert result["rust_standard_library"]["report_compiler"] == COMPILER
    assert result["rust_standard_library"]["text"] == "copyright"
    assert result["licenses"] == ["license text"]


@pytest.mark.parametrize(
    ("before", "after"),
    [("1.99.1", "1.99.2"), ("22.1.0", "23.0.0"), ("a" * 40, "b" * 40)],
)
def test_rejects_different_build_compiler(before: str, after: str) -> None:
    with pytest.raises(ValueError, match="differs from Rust standard library evidence"):
        module._bind(_bundle(), COMPILER.replace(before, after))


def test_rejects_unknown_source_commit() -> None:
    with pytest.raises(ValueError, match="unverified compiler source commit"):
        module._bind(_bundle(), COMPILER.replace("a" * 40, "unknown"))

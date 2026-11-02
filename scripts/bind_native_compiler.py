"""Привязать notices к фактическому компилятору контейнера."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def _identity(text: str) -> dict[str, str]:
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.partition(": ")
        if separator and key in {"release", "commit-hash", "LLVM version"}:
            fields[key] = value
    if set(fields) != {"release", "commit-hash", "LLVM version"}:
        raise ValueError("incomplete compiler identity")
    if not re.fullmatch(r"[0-9a-f]{40}", fields["commit-hash"]):
        raise ValueError("unverified compiler source commit")
    return fields


def _bind(bundle: dict, actual: str) -> bytes:
    if bundle.get("schema_version") != 1:
        raise ValueError("unexpected notice bundle schema")
    original = bundle["rustc"]
    if _identity(original) != _identity(actual):
        raise ValueError("build compiler differs from Rust standard library evidence")
    bundle["rust_standard_library"]["report_compiler"] = original
    bundle["rustc"] = actual
    return (json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def main() -> None:
    """Сохранить compiler record без подмены версии std report."""
    if len(sys.argv) != 3:
        raise SystemExit("usage: bind_native_compiler.py BUNDLE OUTPUT")
    try:
        bundle = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        actual = subprocess.check_output(["rustc", "--version", "--verbose"], text=True)
        data = _bind(bundle, actual)
        with Path(sys.argv[2]).open("xb") as output:
            output.write(data)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc
    print("Native compiler source matches standard library evidence")


if __name__ == "__main__":
    main()

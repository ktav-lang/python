"""Дополнить Cargo bundle сведениями собранного LLVM unwinder."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REVISION = "87f0227cb60147a26a1eeb4fb06e3b505e9c7261"
TARGETS = {"x86_64-unknown-linux-musl", "aarch64-unknown-linux-musl"}


def _file(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"invalid unwinder evidence file: {path.name}")
    data = path.read_bytes()
    if not data or len(data) > 4 * 1024 * 1024:
        raise ValueError(f"invalid unwinder evidence size: {path.name}")
    return {"sha256": hashlib.sha256(data).hexdigest(), "text": data.decode("utf-8")}


def _add(source: Path, archive: Path, target: str, bundle: Path) -> bytes:
    if target not in TARGETS:
        raise ValueError("unexpected musllinux target")
    result = json.loads(bundle.read_text(encoding="utf-8"))
    if result.get("schema_version") != 1 or "native_runtime" in result:
        raise ValueError("unexpected Cargo notice bundle")
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size == 0:
        raise ValueError("missing static LLVM unwinder")
    result["native_runtime"] = {
        "name": "LLVM libunwind",
        "source": "https://github.com/llvm/llvm-project",
        "revision": REVISION,
        "target": target,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "license": _file(source / "LICENSE.TXT"),
        "upstream_credits": "The pinned libunwind tree has no CREDITS.TXT; "
        "its LICENSE.TXT references that file in the legacy terms.",
        "source_modifications": "none",
    }
    return (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def main() -> None:
    """Сохранить тексты уведомлений и происхождение статического архива."""
    if len(sys.argv) != 6:
        raise SystemExit("usage: add_llvm_unwind_notice.py SOURCE ARCHIVE TARGET BUNDLE OUTPUT")
    try:
        data = _add(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
        with Path(sys.argv[5]).open("xb") as output:
            output.write(data)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc)) from exc
    print("LLVM unwinder notice recorded")


if __name__ == "__main__":
    main()

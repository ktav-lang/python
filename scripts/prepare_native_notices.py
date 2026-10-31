"""Подготовить notices существующей locked-сборки."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from cargo_notice_bundle import _build
from collect_cargo_notices import _collect


def _prepare(evidence: Path) -> None:
    root = Path.cwd().resolve()
    lock = root / "Cargo.lock"
    output = root / "python" / "ktav" / "_third_party" / "NOTICE.json"
    evidence = evidence.resolve()
    if not lock.is_file() or lock.is_symlink():
        raise ValueError("missing regular Cargo.lock; resolve dependencies first")
    if evidence.is_relative_to(root):
        raise ValueError("notice evidence must be outside the project source directory")
    if evidence.exists() and (not evidence.is_dir() or any(evidence.iterdir())):
        raise ValueError("notice evidence directory must be empty")
    if output.exists() or output.is_symlink():
        raise ValueError("existing native notice bundle must not be overwritten")
    original_lock = lock.read_bytes()
    raw_metadata = subprocess.check_output(
        ["cargo", "metadata", "--locked", "--all-features", "--format-version", "1"]
    )
    metadata = json.loads(raw_metadata)
    for package in metadata["packages"]:
        source = Path(package["manifest_path"]).resolve().parent
        if evidence.is_relative_to(source):
            raise ValueError("notice evidence must be outside every Cargo package source")
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "Cargo.lock").write_bytes(original_lock)
    (evidence / "metadata.json").write_bytes(raw_metadata)
    rustc = subprocess.check_output(["rustc", "--version", "--verbose"])
    (evidence / "rustc.txt").write_bytes(rustc)
    sysroot = subprocess.check_output(["rustc", "--print", "sysroot"], text=True).strip()
    shutil.copyfile(
        Path(sysroot) / "share" / "doc" / "rust" / "COPYRIGHT-library.html",
        evidence / "COPYRIGHT-library.html",
    )
    raw_licenses = subprocess.check_output(
        [
            "cargo",
            "about",
            "generate",
            "--locked",
            "--all-features",
            "--fail",
            "--config",
            "ci/about.toml",
            "--format",
            "json",
        ]
    )
    (evidence / "licenses.json").write_bytes(raw_licenses)
    notices = _collect(metadata, json.loads(raw_licenses))
    (evidence / "notices.json").write_text(
        json.dumps(notices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    data = _build(evidence)
    if lock.read_bytes() != original_lock:
        raise ValueError("Cargo.lock changed while generating notices")
    (evidence / "NOTICE.json").write_bytes(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as destination:
        destination.write(data)
    print(f"Locked native notice bundle prepared for {len(metadata['packages'])} packages")


def main() -> None:
    """Подготовить evidence без изменения Cargo.lock и версии core."""
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_native_notices.py EMPTY_EVIDENCE_DIRECTORY")
    try:
        _prepare(Path(sys.argv[1]))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()

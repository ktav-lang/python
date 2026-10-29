"""Проверить уведомления внешнего статического unwinder."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "add_llvm_unwind_notice.py"


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "LICENSE.TXT").write_bytes(b"Full license\r\nLegacy terms\n")
    archive = tmp_path / "libunwind.a"
    archive.write_bytes(b"static archive")
    bundle = tmp_path / "cargo.json"
    bundle.write_text(
        json.dumps({"schema_version": 1, "licenses": ["Cargo text"]}), encoding="utf-8"
    )
    return source, archive, bundle


def _run(
    source: Path,
    archive: Path,
    bundle: Path,
    output: Path,
    target: str = "x86_64-unknown-linux-musl",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), str(archive), target, str(bundle), str(output)],
        capture_output=True,
        text=True,
    )


def test_preserves_license_and_binds_archive(tmp_path: Path) -> None:
    source, archive, bundle = _inputs(tmp_path)
    output = tmp_path / "result.json"
    result = _run(source, archive, bundle, output)
    assert result.returncode == 0, result.stderr
    content = json.loads(output.read_bytes())
    assert content["licenses"] == ["Cargo text"]
    runtime = content["native_runtime"]
    assert runtime["license"]["text"] == "Full license\r\nLegacy terms\n"
    assert runtime["archive_sha256"] == hashlib.sha256(archive.read_bytes()).hexdigest()
    assert runtime["revision"] == "87f0227cb60147a26a1eeb4fb06e3b505e9c7261"
    assert str(tmp_path) not in output.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["LICENSE.TXT", "archive", "target", "existing runtime"])
def test_rejects_incomplete_or_overwritten_evidence(tmp_path: Path, name: str) -> None:
    source, archive, bundle = _inputs(tmp_path)
    target = "x86_64-unknown-linux-musl"
    if name == "LICENSE.TXT":
        (source / name).write_bytes(b"")
    elif name == "archive":
        archive.write_bytes(b"")
    elif name == "target":
        target = "unknown"
    else:
        bundle.write_text(json.dumps({"schema_version": 1, "native_runtime": {}}), encoding="utf-8")
    output = tmp_path / "result.json"
    result = _run(source, archive, bundle, output, target)
    assert result.returncode != 0
    assert not output.exists()

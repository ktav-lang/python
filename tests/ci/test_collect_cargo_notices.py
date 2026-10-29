"""Проверить инвентаризацию Cargo notices."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "collect_cargo_notices.py"


def _inputs(tmp_path: Path) -> tuple[Path, dict, dict]:
    source = tmp_path / "crate"
    source.mkdir()
    (source / "Cargo.toml").write_text("[package]\n", encoding="utf-8")
    package = {
        "id": "registry+example#fixture@1.0.0",
        "name": "fixture",
        "version": "1.0.0",
        "source": "registry+example",
        "manifest_path": str(source / "Cargo.toml"),
    }
    metadata = {"packages": [package]}
    report = {
        "crates": [{"package": {"id": package["id"]}}],
        "licenses": [
            {"source_path": "LICENSE", "text": "license", "used_by": [{"crate": package}]}
        ],
    }
    return source, metadata, report


def _run(
    tmp_path: Path, metadata: dict, report: dict
) -> tuple[subprocess.CompletedProcess[str], Path]:
    metadata_path = tmp_path / "metadata.json"
    report_path = tmp_path / "licenses.json"
    output_path = tmp_path / "notices.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(CHECKER), str(metadata_path), str(report_path), str(output_path)],
        capture_output=True,
        text=True,
    )
    return result, output_path


def test_collects_nested_notices_with_hashes(tmp_path: Path) -> None:
    source, metadata, report = _inputs(tmp_path)
    (source / "nested").mkdir()
    (source / "nested" / "NOTICE.txt").write_text("notice text", encoding="utf-8")
    (source / "COPYRIGHT").write_text("copyright text", encoding="utf-8")
    (source / "target").mkdir()
    (source / "target" / "NOTICE").write_text("ignored", encoding="utf-8")
    result, output = _run(tmp_path, metadata, report)
    assert result.returncode == 0, result.stderr
    collected = json.loads(output.read_text(encoding="utf-8"))
    assert collected["package_count"] == 1
    notices = {entry["path"]: entry for entry in collected["notices"]}
    assert set(notices) == {"COPYRIGHT", "nested/NOTICE.txt"}
    assert notices["nested/NOTICE.txt"]["text"] == "notice text"
    assert notices["nested/NOTICE.txt"]["sha256"] == hashlib.sha256(b"notice text").hexdigest()


def test_rejects_uncovered_package(tmp_path: Path) -> None:
    _, metadata, report = _inputs(tmp_path)
    report["licenses"][0]["used_by"] = []
    result, output = _run(tmp_path, metadata, report)
    assert result.returncode != 0
    assert "coverage differ" in result.stderr
    assert not output.exists()


def test_rejects_generic_license_fallback(tmp_path: Path) -> None:
    _, metadata, report = _inputs(tmp_path)
    report["licenses"][0]["source_path"] = None
    result, output = _run(tmp_path, metadata, report)
    assert result.returncode != 0
    assert "unverified fallback" in result.stderr
    assert not output.exists()


def test_rejects_non_utf8_notice(tmp_path: Path) -> None:
    source, metadata, report = _inputs(tmp_path)
    (source / "NOTICE").write_bytes(b"\xff")
    result, output = _run(tmp_path, metadata, report)
    assert result.returncode != 0
    assert not output.exists()


def test_rejects_linked_notice(tmp_path: Path) -> None:
    source, metadata, report = _inputs(tmp_path)
    external = tmp_path / "external"
    external.write_text("outside", encoding="utf-8")
    try:
        (source / "NOTICE").symlink_to(external)
    except OSError:
        pytest.skip("symlinks unavailable")
    result, output = _run(tmp_path, metadata, report)
    assert result.returncode != 0
    assert "unverified symlink" in result.stderr
    assert not output.exists()

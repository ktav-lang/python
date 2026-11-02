"""Проверить упаковку лицензионных уведомлений внутри wheel."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "cargo_notice_bundle.py"
MEMBER = "ktav/_third_party/NOTICE.json"


def _run(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True
    )


def _evidence(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "NOTICE").write_bytes(b"Third-party copyright\r\n")
    package = {
        "id": "registry+example#fixture@1.0.0",
        "name": "fixture",
        "version": "1.0.0",
        "source": "registry+example",
        "manifest_path": str(source / "Cargo.toml"),
    }
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    (evidence / "metadata.json").write_text(json.dumps({"packages": [package]}), encoding="utf-8")
    report = {
        "crates": [{"package": {"id": package["id"]}}],
        "licenses": [
            {
                "source_path": str(source / "LICENSE"),
                "text": "MIT copyright\n",
                "used_by": [{"crate": package}],
            }
        ],
    }
    (evidence / "licenses.json").write_text(json.dumps(report), encoding="utf-8")
    (evidence / "Cargo.lock").write_bytes(b"version = 4\n")
    (evidence / "rustc.txt").write_bytes(b"rustc fixture\ncommit-hash: abc\n")
    (evidence / "COPYRIGHT-library.html").write_bytes(b"<html>Rust copyright</html>\r\n")
    return evidence


def _wheel(tmp_path: Path, data: bytes, *, corrupt_record: bool = False) -> Path:
    path = tmp_path / "fixture.whl"
    record = io.StringIO(newline="")
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    csv.writer(record, lineterminator="\n").writerow(
        [MEMBER, "sha256=wrong" if corrupt_record else f"sha256={digest}", str(len(data))]
    )
    with zipfile.ZipFile(path, "w") as wheel:
        wheel.writestr(MEMBER, data)
        wheel.writestr("ktav-1.0.dist-info/RECORD", record.getvalue())
    return path


def test_build_preserves_text_and_omits_local_paths(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    for output in (first, second):
        result = _run("build", evidence, output)
        assert result.returncode == 0, result.stderr
    assert first.read_bytes() == second.read_bytes()
    bundle = json.loads(first.read_bytes())
    assert str(tmp_path) not in first.read_text(encoding="utf-8")
    assert "manifest_path" not in bundle["packages"][0]
    assert bundle["licenses"][0]["text"] == "MIT copyright\n"
    assert bundle["notices"][0]["text"] == "Third-party copyright\r\n"
    assert bundle["rust_standard_library"]["text"] == "<html>Rust copyright</html>\r\n"
    assert bundle["cargo_lock_sha256"] == hashlib.sha256(b"version = 4\n").hexdigest()
    assert "not a linked-code inventory" in bundle["coverage"]
    result = _run("verify", _wheel(tmp_path, first.read_bytes()), first)
    assert result.returncode == 0, result.stderr


def test_build_rejects_fallback(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)
    path = evidence / "licenses.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report["licenses"][0]["source_path"] = None
    path.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "bundle.json"
    assert _run("build", evidence, output).returncode != 0
    assert not output.exists()


@pytest.mark.parametrize("name", ["Cargo.lock", "rustc.txt", "COPYRIGHT-library.html"])
def test_build_rejects_empty_provenance(tmp_path: Path, name: str) -> None:
    evidence = _evidence(tmp_path)
    (evidence / name).write_bytes(b"")
    assert _run("build", evidence, tmp_path / "bundle.json").returncode != 0


def test_verify_rejects_modified_bundle(tmp_path: Path) -> None:
    expected = tmp_path / "expected.json"
    expected.write_bytes(b"original")
    result = _run("verify", _wheel(tmp_path, b"modified"), expected)
    assert result.returncode != 0
    assert "differs from build evidence" in result.stderr


def test_verify_rejects_corrupt_record(tmp_path: Path) -> None:
    expected = tmp_path / "expected.json"
    expected.write_bytes(b"bundle")
    result = _run("verify", _wheel(tmp_path, b"bundle", corrupt_record=True), expected)
    assert result.returncode != 0
    assert "does not match wheel RECORD" in result.stderr


def test_verify_rejects_missing_bundle(tmp_path: Path) -> None:
    expected = tmp_path / "expected.json"
    expected.write_bytes(b"bundle")
    path = tmp_path / "empty.whl"
    with zipfile.ZipFile(path, "w"):
        pass
    result = _run("verify", path, expected)
    assert result.returncode != 0
    assert "missing, duplicate or wrong-sized" in result.stderr


def test_verify_rejects_duplicate_bundle(tmp_path: Path) -> None:
    expected = tmp_path / "expected.json"
    expected.write_bytes(b"bundle")
    path = _wheel(tmp_path, b"bundle")
    with pytest.warns(UserWarning, match="Duplicate name"), zipfile.ZipFile(path, "a") as wheel:
        wheel.writestr(MEMBER, b"bundle")
    result = _run("verify", path, expected)
    assert result.returncode != 0
    assert "missing, duplicate or wrong-sized" in result.stderr

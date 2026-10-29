"""Проверить защиту musllinux wheel от неверного состава."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts" / "check_musllinux_wheel.py"
MODULE = "ktav/_core.abi3.so"


def _wheel(tmp_path: Path, *, extra: str | None = None, corrupt: bool = False) -> Path:
    path = tmp_path / "ktav-0.8.1-cp39-abi3-musllinux_1_2_x86_64.whl"
    data = b"not an ELF file"
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    record = io.StringIO(newline="")
    csv.writer(record, lineterminator="\n").writerow(
        [MODULE, "sha256=wrong" if corrupt else f"sha256={digest}", str(len(data))]
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(MODULE, data)
        archive.writestr("ktav-0.8.1.dist-info/RECORD", record.getvalue())
        if extra:
            archive.writestr(extra, b"additional binary")
    return path


def _run(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECKER), str(path)], capture_output=True, text=True)


def test_rejects_bundled_libgcc(tmp_path: Path) -> None:
    result = _run(_wheel(tmp_path, extra="ktav.libs/libgcc_s-abcd.so.1"))
    assert result.returncode != 0
    assert "unexpected wheel native payload" in result.stderr


def test_rejects_corrupt_record(tmp_path: Path) -> None:
    result = _run(_wheel(tmp_path, corrupt=True))
    assert result.returncode != 0
    assert "does not match wheel RECORD" in result.stderr


def test_rejects_duplicate_native_module(tmp_path: Path) -> None:
    path = _wheel(tmp_path)
    with pytest.warns(UserWarning, match="Duplicate name"):
        with zipfile.ZipFile(path, "a") as archive:
            archive.writestr(MODULE, b"duplicate")
    result = _run(path)
    assert result.returncode != 0
    assert "unexpected wheel native payload" in result.stderr

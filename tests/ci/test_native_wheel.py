"""Проверить переносимые native wheel guards."""

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

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_native_wheel.py"
NOTICE = "ktav/_third_party/NOTICE.json"


def _run(wheel: Path, bundle: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(wheel), str(bundle), str(bundle.parent / "report.txt")],
        capture_output=True,
        text=True,
    )


def _wheel(tmp_path: Path, platform: str, module: str, extra: str | None) -> tuple[Path, Path]:
    wheel = tmp_path / f"ktav-0.8.1-cp39-abi3-{platform}.whl"
    bundle = tmp_path / "NOTICE.json"
    bundle.write_bytes(b"bundle")
    payload = {NOTICE: b"bundle", module: b"not a native binary"}
    if extra:
        payload[extra] = b"unexpected"
    rows = io.StringIO(newline="")
    writer = csv.writer(rows, lineterminator="\n")
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            writer.writerow([name, f"sha256={digest}", str(len(data))])
        archive.writestr("ktav-0.8.1.dist-info/RECORD", rows.getvalue())
    return wheel, bundle


@pytest.mark.parametrize(
    ("platform", "module"),
    [
        ("win_amd64", "ktav/_core.pyd"),
        ("manylinux_2_17_x86_64", "ktav/_core.abi3.so"),
        ("macosx_11_0_arm64", "ktav/_core.abi3.so"),
    ],
)
def test_rejects_wrong_native_format(tmp_path: Path, platform: str, module: str) -> None:
    result = _run(*_wheel(tmp_path, platform, module, None))
    assert result.returncode != 0
    assert "native payload format differs" in result.stderr


def test_rejects_additional_runtime_dll(tmp_path: Path) -> None:
    result = _run(*_wheel(tmp_path, "win_amd64", "ktav/_core.pyd", "ktav/runtime.dll"))
    assert result.returncode != 0
    assert "unexpected wheel native payload" in result.stderr


def test_rejects_unexpected_abi_tag(tmp_path: Path) -> None:
    result = _run(tmp_path / "ktav-0.8.1-cp312-cp312-win_amd64.whl", tmp_path / "NOTICE.json")
    assert result.returncode != 0
    assert "unexpected native wheel ABI tag" in result.stderr

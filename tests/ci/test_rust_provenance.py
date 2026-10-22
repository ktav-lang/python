"""Negative regressions for scripts/check_rust_provenance.py.

Runs the checker as a subprocess against hand-written fixture manifests
and locks under pytest tmp_path; no repo files are read or mutated.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_rust_provenance.py"

CHECKSUM = "7140dfe2fa6c320e74768cd6a637828c2d26f81746254f4fcd805f3993bd3fd5"

SOURCE = "registry+https://github.com/rust-lang/crates.io-index"


def manifest_text(ktav_req: str = ">=0.8.1, <0.9", version: str = "0.8.1") -> str:
    return (
        f'[package]\nname = "ktav-workspace"\nversion = "{version}"\n\n'
        f'[dependencies]\nktav = "{ktav_req}"\n'
    )


def lock_text(
    version: str = "0.8.1",
    source: str = SOURCE,
    checksum: str = CHECKSUM,
) -> str:
    return (
        'version = 4\n\n[[package]]\nname = "ktav"\n'
        f'version = "{version}"\nsource = "{source}"\nchecksum = "{checksum}"\n'
    )


def run_checker(tmp_path: Path, manifest: str, lock: str | None):
    m = tmp_path / "Cargo.toml"
    m.write_text(manifest, encoding="utf-8")
    cmd = [sys.executable, str(SCRIPT), "--cargo-manifest", str(m)]
    if lock is None:
        cmd += ["--cargo-lock", str(tmp_path / "Cargo.lock")]
    else:
        lp = tmp_path / "Cargo.lock"
        lp.write_text(lock, encoding="utf-8")
        cmd += ["--cargo-lock", str(lp)]
    return subprocess.run(cmd, capture_output=True)


def test_valid_fixture_passes(tmp_path: Path) -> None:
    assert run_checker(tmp_path, manifest_text(), lock_text()).returncode == 0


def test_missing_lock_fails(tmp_path: Path) -> None:
    r = run_checker(tmp_path, manifest_text(), None)
    assert r.returncode != 0
    assert b"Cargo.lock" in r.stderr


def test_wrong_lock_version_fails(tmp_path: Path) -> None:
    r = run_checker(tmp_path, manifest_text(), lock_text(version="0.8.2"))
    assert r.returncode != 0


def test_wrong_source_fails(tmp_path: Path) -> None:
    r = run_checker(tmp_path, manifest_text(), lock_text(source="registry+https://example.test"))
    assert r.returncode != 0


def test_wrong_checksum_fails(tmp_path: Path) -> None:
    bad = "0" * 64
    r = run_checker(tmp_path, manifest_text(), lock_text(checksum=bad))
    assert r.returncode != 0


@pytest.mark.parametrize("req", ["=0.8.1", ">=0.8.1"])
def test_wrong_public_range_fails(tmp_path: Path, req: str) -> None:
    r = run_checker(tmp_path, manifest_text(ktav_req=req), lock_text())
    assert r.returncode != 0


def test_manifest_without_package_version_fails(tmp_path: Path) -> None:
    text = '[package]\nname = "ktav-workspace"\n\n[dependencies]\nktav = ">=0.8.1, <0.9"\n'
    r = run_checker(tmp_path, text, lock_text())
    assert r.returncode != 0

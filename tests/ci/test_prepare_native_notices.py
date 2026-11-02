"""Проверить защиту подготовки release notices."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "prepare_native_notices.py"


def _run(project: Path, evidence: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(evidence)],
        cwd=project,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("condition", ["missing lock", "nested evidence", "nonempty", "bundle"])
def test_rejects_unsafe_staging_before_cargo(tmp_path: Path, condition: str) -> None:
    project = tmp_path / "project"
    project.mkdir()
    evidence = tmp_path / "evidence"
    if condition != "missing lock":
        (project / "Cargo.lock").write_bytes(b"version = 4\n")
    if condition == "nested evidence":
        evidence = project / "evidence"
    elif condition == "nonempty":
        evidence.mkdir()
        (evidence / "keep.txt").write_bytes(b"preserve")
    elif condition == "bundle":
        bundle = project / "python" / "ktav" / "_third_party" / "NOTICE.json"
        bundle.parent.mkdir(parents=True)
        bundle.write_bytes(b"preserve")
    result = _run(project, evidence)
    assert result.returncode != 0
    expected = {
        "missing lock": "missing regular Cargo.lock",
        "nested evidence": "outside the project source directory",
        "nonempty": "evidence directory must be empty",
        "bundle": "existing native notice bundle",
    }
    assert expected[condition] in result.stderr
    if condition == "nonempty":
        assert (evidence / "keep.txt").read_bytes() == b"preserve"
    if condition == "bundle":
        assert bundle.read_bytes() == b"preserve"
    if condition != "missing lock":
        assert (project / "Cargo.lock").read_bytes() == b"version = 4\n"

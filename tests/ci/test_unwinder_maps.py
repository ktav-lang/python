"""Проверить различение входных объектов и шаблонов линкера."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_unwinder_maps.py"
BASE = "LOAD /work/libunwind.a\n/work/libunwind.a(UnwindLevel1.c.o)\n"


def _run(tmp_path: Path, extra: str) -> subprocess.CompletedProcess[str]:
    for name in ("link.wheel", "link.probe"):
        (tmp_path / name).write_text(BASE + extra, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True
    )


def test_accepts_unused_crt_patterns_and_archives(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        " *(.init_array EXCLUDE_FILE(*crtend?.o *crtbegin.o) .ctors)\n"
        " *crtbegin.o(.ctors)\nLOAD /tool/libgcc.a\nLOAD /tool/libgcc_eh.a\n",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "entry",
    [
        "LOAD /tool/crtbeginS.o\n",
        "LOAD /tool/crtendS.o\n",
        "LOAD crtbegin.o\n",
        "/tool/libgcc.a(helper.o)\n",
        "/tool/libgcc_eh.a(unwind-dw2.o)\n",
    ],
)
def test_rejects_actual_gcc_inputs(tmp_path: Path, entry: str) -> None:
    result = _run(tmp_path, entry)
    assert result.returncode != 0
    assert "GCC runtime input linked" in result.stderr


def test_rejects_missing_probe_map(tmp_path: Path) -> None:
    (tmp_path / "link.wheel").write_text(BASE, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path)], capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "missing wheel or panic probe" in result.stderr

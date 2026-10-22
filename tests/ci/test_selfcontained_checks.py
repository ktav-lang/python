"""Regression tests for the self-contained pure-wheel CI checks."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from email.message import Message
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INSTALLED = ROOT / "scripts" / "check_installed_pure.py"
METADATA = ROOT / "scripts" / "check_pure_wheel_metadata.py"


def test_installed_guard_denies_third_party_and_runtime_access(tmp_path: Path) -> None:
    package = tmp_path / "forbidden_pkg"
    package.mkdir()
    sentinel = tmp_path / "imported"
    (package / "__init__.py").write_text(
        f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('ran')\n", encoding="utf-8"
    )
    child = r"""
import importlib, pathlib, runpy, socket, subprocess, sys
checker = runpy.run_path(sys.argv[1], run_name="ci_guard_definitions")
sys.path.insert(0, sys.argv[2])
sys.meta_path.insert(0, checker["BlockCore"]())
checker["install_runtime_guards"]()
for load in (lambda: __import__("forbidden_pkg"), lambda: importlib.import_module("forbidden_pkg")):
    try:
        load()
    except ModuleNotFoundError as exc:
        assert "third-party import" in str(exc), str(exc)
        assert exc.name == "forbidden_pkg", exc.name
    else:
        raise AssertionError("third-party package was imported")
assert not pathlib.Path(sys.argv[3]).exists(), "denied package body ran"
try:
    __import__("ktav._core")
except ImportError as exc:
    assert "ktav._core blocked" in str(exc)
else:
    raise AssertionError("native module was allowed")
for action in (
    lambda: socket.create_connection(("127.0.0.1", 1)),
    lambda: subprocess.Popen([sys.executable, "-c", "pass"]),
):
    try:
        action()
    except AssertionError as exc:
        assert "network or subprocess" in str(exc)
    else:
        raise AssertionError("runtime operation was allowed")
"""
    result = subprocess.run(
        [sys.executable, "-c", child, str(INSTALLED), str(tmp_path), str(sentinel)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_installed_guard_allows_stdlib_and_source_pure_package() -> None:
    child = r"""
import runpy, sys
checker = runpy.run_path(sys.argv[1], run_name="ci_guard_definitions")
sys.path.insert(0, sys.argv[2])
sys.meta_path.insert(0, checker["BlockCore"]())
checker["install_runtime_guards"]()
import json
import ktav.pure
assert json.loads('{"ok": true}') == {"ok": True}
assert ktav.pure.loads("answer: 42") == {"answer": 42}
"""
    result = subprocess.run(
        [sys.executable, "-c", child, str(INSTALLED), str(ROOT / "python")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def wheel(tmp_path: Path, *metadata: bytes) -> Path:
    path = tmp_path / "fixture.whl"
    with zipfile.ZipFile(path, "w") as archive:
        for index, body in enumerate(metadata):
            name = (
                "ktav-0.8.1.dist-info/METADATA"
                if index == 0
                else f"extra-{index}.dist-info/METADATA"
            )
            archive.writestr(name, body)
    return path


def metadata_text(*fields: tuple[str, str]) -> bytes:
    message = Message()
    for key, value in fields:
        message[key] = value
    return str(message).encode()


def run_metadata(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(METADATA), str(path)], capture_output=True, text=True
    )


def test_wheel_metadata_accepts_valid_pure_wheel(tmp_path: Path) -> None:
    path = wheel(
        tmp_path, metadata_text(("Metadata-Version", "2.4"), ("Name", "ktav"), ("Version", "0.8.1"))
    )
    result = run_metadata(path)
    assert result.returncode == 0, result.stderr
    assert "metadata OK" in result.stdout


def test_wheel_metadata_rejects_dependencies(tmp_path: Path) -> None:
    path = wheel(
        tmp_path,
        metadata_text(
            ("Metadata-Version", "2.4"),
            ("Name", "ktav"),
            ("Version", "0.8.1"),
            ("Requires-Dist", "other"),
        ),
    )
    result = run_metadata(path)
    assert result.returncode != 0
    assert "must declare no Requires-Dist" in result.stderr


@pytest.mark.parametrize(
    ("name", "version"),
    [("other", "0.8.1"), ("ktav", "0.8.2")],
)
def test_wheel_metadata_rejects_wrong_identity(tmp_path: Path, name: str, version: str) -> None:
    path = wheel(
        tmp_path, metadata_text(("Metadata-Version", "2.4"), ("Name", name), ("Version", version))
    )
    result = run_metadata(path)
    assert result.returncode != 0
    assert "expected ktav 0.8.1 Name/Version metadata" in result.stderr


def test_wheel_metadata_rejects_missing_metadata(tmp_path: Path) -> None:
    result = run_metadata(wheel(tmp_path))
    assert result.returncode != 0
    assert "expected exactly one root .dist-info/METADATA" in result.stderr


def test_wheel_metadata_rejects_duplicate_metadata(tmp_path: Path) -> None:
    valid = metadata_text(("Metadata-Version", "2.4"), ("Name", "ktav"), ("Version", "0.8.1"))
    path = wheel(tmp_path, valid, valid)
    result = run_metadata(path)
    assert result.returncode != 0
    assert "expected exactly one root .dist-info/METADATA" in result.stderr

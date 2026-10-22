"""Pure-only units for the public ``ktav.pure`` module surface.

The spec-corpus categories for the pure backend run (parametrized) in
``tests/test_conformance.py``; this file covers what that runner does
not: version markers, the raw-bytes InvalidUtf8 span contract, the file
wrappers, and the no-native import scenarios.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import ktav
import pytest
from ktav import pure

REPO = Path(__file__).resolve().parents[2]

# A sys.meta_path probe run in a FRESH interpreter: blocks ktav._core
# (whether or not it is installed in that environment), then asserts
# that `import ktav` succeeds, `import ktav.pure` fully works, and
# calling a native-backed top-level function raises the documented clean
# ImportError pointing at ktav.pure. Written as a module (not -c) so the
# quoting survives Windows.
PROBE = Path(__file__).parent / "_no_native_probe.py"

FIELDS = (
    "error",
    "reason",
    "line",
    "line_text",
    "span",
    "path",
    "body",
    "canonical",
    "spec_section",
    "message",
)


def test_version_markers() -> None:
    assert pure.__version__ == "0.8.1"
    assert pure.__spec_version__ == "0.8.1"


def test_public_surface_mirrors_the_native_module() -> None:
    for name in (
        "loads",
        "loads_strict",
        "dumps",
        "emit_canonical",
        "dumps_force_strings",
        "format",
        "canonical_from_source",
        "KtavError",
        "KtavDecodeError",
        "KtavEncodeError",
        "__version__",
        "__spec_version__",
    ):
        assert hasattr(pure, name), f"ktav.pure is missing {name}"


def test_all_ten_envelope_fields_present_on_a_pure_decode_error() -> None:
    with pytest.raises(pure.KtavDecodeError) as excinfo:
        pure.loads("x: [")
    error = excinfo.value
    for field in FIELDS:
        assert hasattr(error, field), f"missing attribute {field}"
    assert str(error) == error.message
    assert error.message


def test_all_ten_envelope_fields_present_on_a_pure_encode_error() -> None:
    with pytest.raises(pure.KtavEncodeError) as excinfo:
        pure.dumps({"v": float("nan")})
    error = excinfo.value
    for field in FIELDS:
        assert hasattr(error, field), f"missing attribute {field}"
    assert error.reason == "NonFiniteFloat"
    assert str(error) == error.message


def test_strict_lossy_envelope_payloads() -> None:
    with pytest.raises(pure.KtavDecodeError) as excinfo:
        pure.loads_strict("a: 1.10\n")
    error = excinfo.value
    assert error.error == "LossyScalar"
    assert error.body == "1.10"
    assert error.canonical == "1.1"
    assert error.spec_section == "§3.6/§5.2"


def test_invalid_utf8_bytes_raise_invalidutf8_with_a_nonempty_span() -> None:
    """§ 6.15: the pure backend validates raw bytes BEFORE any grammar work.

    The native wrapper decodes bytes itself (UnicodeDecodeError), so this
    byte-level contract is pure-specific by construction.
    """
    raw = b"a: \xff\xfe\n"
    with pytest.raises(pure.KtavDecodeError) as excinfo:
        pure.loads(raw)
    error = excinfo.value
    assert error.error == "InvalidUtf8"
    assert error.span is not None
    assert error.span["end"] > error.span["start"], "span must cover the malformed bytes"
    assert b"a: "[:3] == b"a: "  # the malformed run starts after the valid prefix
    assert 0 < error.span["start"] < len(raw)


def test_file_wrappers() -> None:

    assert pure.load(io.StringIO("a: 1\n")) == {"a": 1}
    out = io.StringIO()
    pure.dump({"a": 1}, out)
    assert out.getvalue() == "a: 1\n"
    assert pure.load(io.BytesIO(b"a: 1\n")) == {"a": 1}
    out_bytes = io.BytesIO()
    pure.dump({"a": 1}, out_bytes)
    assert out_bytes.getvalue() == b"a: 1\n"

    with pytest.raises(pure.KtavDecodeError):
        pure.loads("x: [")
    with pytest.raises(pure.KtavEncodeError):
        pure.dumps(object())


def _run_probe() -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "python")
    return subprocess.run(
        [sys.executable, str(PROBE)],
        capture_output=True,
        timeout=120,
        env=env,
    )


def test_no_native_scenario_in_a_fresh_interpreter() -> None:
    """`import ktav` never fails without _core; native calls raise the clean
    ImportError; ktav.pure works fully. Runs even where _core IS installed
    (the regular test job) because the probe blocks it via sys.meta_path."""
    result = _run_probe()
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    assert result.stdout.strip() == b"ok"


def test_native_install_pure_import_never_probes_core_and_native_default_is_preserved() -> None:
    """Fresh-process checks for pure isolation and the explicit native default."""
    script = r"""
import importlib.abc
import sys

class Tripwire(importlib.abc.MetaPathFinder):
    attempts = 0
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "ktav._core":
            self.attempts += 1
            raise AssertionError("pure import attempted ktav._core")
        return None

tripwire = Tripwire()
sys.meta_path.insert(0, tripwire)
import ktav
from ktav import pure
import ktav.pure
import io
assert tripwire.attempts == 0
assert "ktav._core" not in sys.modules
assert pure.loads("a: 1") == {"a": 1}
assert pure.loads_strict("a: 1.0") == {"a": 1.0}
assert pure.dumps({"a": [1, "x", True, None]})
assert pure.emit_canonical({"a": 1})
assert pure.dumps_force_strings({"a": 1})
assert pure.format("a: 1") == "a: 1\n"
assert pure.canonical_from_source("a: 1")
assert pure.load(io.StringIO("a: 1")) == {"a": 1}
out = io.StringIO()
pure.dump({"a": 1}, out)
assert out.getvalue() == "a: 1\n"
try:
    pure.loads("x: [")
except pure.KtavDecodeError:
    pass
else:
    raise AssertionError("malformed input was accepted")
try:
    pure.dumps(object())
except pure.KtavEncodeError:
    pass
else:
    raise AssertionError("unsupported root was accepted")
assert tripwire.attempts == 0
assert "ktav._core" not in sys.modules
"""
    env = dict(os.environ)
    installed_paths = tuple(
        Path(path).resolve()
        for path in (sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))
        if path
    )
    package_path = Path(ktav.__file__).resolve()
    from_installed_package = any(package_path.is_relative_to(path) for path in installed_paths)
    if not ktav._HAS_CORE or not from_installed_package:
        env["PYTHONPATH"] = str(REPO / "python")
    else:
        env.pop("PYTHONPATH", None)
        script = script.replace(
            "import ktav\nfrom ktav import pure\n",
            "import ktav\n"
            "import pathlib, sysconfig\n"
            "paths = [sysconfig.get_path('purelib'), sysconfig.get_path('platlib')]\n"
            "package = pathlib.Path(ktav.__file__).resolve()\n"
            "assert any(package.is_relative_to(pathlib.Path(p).resolve()) for p in paths if p)\n"
            "from ktav import pure\n",
            1,
        )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, timeout=120, env=env
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")

    if not ktav._HAS_CORE:
        return
    native_script = r"""
import io
import ktav
import ktav._core as core
assert ktav._HAS_CORE is True
root_out = io.StringIO()
ktav.dump({"a": 1}, root_out)
assert root_out.getvalue() == "a: 1\n"
assert ktav.KtavDecodeError is core.KtavDecodeError
assert ktav.loads("a: 1") == {"a": 1}
try:
    ktav.loads("x: [")
except core.KtavDecodeError:
    pass
else:
    raise AssertionError("malformed native input was accepted")
assert ktav.KtavDecodeError is core.KtavDecodeError
"""
    result = subprocess.run(
        [sys.executable, "-c", native_script],
        capture_output=True,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")

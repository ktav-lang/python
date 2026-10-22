"""Pure-only units for the public ``ktav.pure`` module surface.

The spec-corpus categories for the pure backend run (parametrized) in
``tests/test_conformance.py``; this file covers what that runner does
not: version markers, the raw-bytes InvalidUtf8 span contract, the file
wrappers, and the no-native import scenarios.
"""

from __future__ import annotations

import os
import subprocess
import sys
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
    import io

    assert pure.load(io.StringIO("a: 1\n")) == {"a": 1}
    out = io.StringIO()
    pure.dump({"a": 1}, out)
    assert out.getvalue() == "a: 1\n"
    assert pure.load(io.BytesIO(b"a: 1\n")) == {"a": 1}
    out_bytes = io.BytesIO()
    pure.dump({"a": 1}, out_bytes)
    assert out_bytes.getvalue() == b"a: 1\n"


@pytest.mark.skipif(
    ktav._HAS_CORE,
    reason="no-native import behaviour is exercised in a blocked subprocess anyway",
)
def test_import_ktav_without_core_gives_pure_classes() -> None:
    """In a genuinely native-free process (pure-mode CI job) the top-level
    package still exposes the pure exception classes and pure still works,
    while a NATIVE function raises the documented clean ImportError
    pointing at ktav.pure (ktav/__init__.py's no-core branch)."""
    assert not hasattr(ktav, "_core")
    assert not ktav._HAS_CORE
    assert ktav.KtavDecodeError is pure.KtavDecodeError
    with pytest.raises(ImportError) as exc_info:
        ktav.loads("a: 1")
    # Public contract of ktav/__init__.py's no-core stub: the message
    # must contain BOTH the import fix ("from ktav import pure") and the
    # backend name ("ktav.pure").
    assert "from ktav import pure" in str(exc_info.value)
    assert "ktav.pure" in str(exc_info.value)
    assert pure.loads("a: 1") == {"a": 1}


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

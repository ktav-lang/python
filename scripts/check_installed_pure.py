"""Packaged no-native scenario: full corpus through ktav.pure, wheel-installed.

Runs the FULL spec corpus through ``ktav.pure`` from an INSTALLED wheel,
with ``ktav._core`` hard-blocked via ``sys.meta_path`` (so even a wheel
that bundles the compiled extension cannot be used) and with the
checkout's ``python/`` directory deliberately NOT on ``sys.path`` — the
module under test is the one pip installed, not the source tree.

Fail-closed: missing corpus, missing manifest, wrong schema_version,
wrong § 8.5 counts, unknown fixture_flags, a backend that is not fully
functional, or any blocked-native leak is a non-zero exit, never a skip.

Usage: python scripts/check_installed_pure.py [spec-tests-dir]
       (default: spec/versions/0.8/tests relative to the repo root)
"""

from __future__ import annotations

import json
import sys
import sysconfig
from importlib.machinery import FrozenImporter, PathFinder
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STDLIB_PATHS = tuple(
    Path(sysconfig.get_path(key)).resolve()
    for key in ("stdlib", "platstdlib")
    if sysconfig.get_path(key)
)
SITE_PATHS = tuple(
    Path(path).resolve() for key in ("purelib", "platlib") if (path := sysconfig.get_path(key))
)
DESTSHARED = sysconfig.get_config_var("DESTSHARED")
EXTENSION_PATH = Path(DESTSHARED).resolve() if DESTSHARED else None
WINDOWS_EXTENSION_PATH = (
    Path(sys.base_prefix).resolve() / "DLLs" if sys.platform == "win32" else None
)
INVENTORY = {
    "valid": 228,
    "invalid": 90,
    "unrepresentable": 5,
    "parseable-unrepresentable": 4,
    "strict-lossy": 13,
}

# Closed decode-category set — mirror of ktav._pure.errors.SPEC_SECTIONS
# keys. The installed script cannot import the source tree (the module
# under test is the installed wheel), so the set is pinned here and kept
# in sync by review; an oracle naming anything else is a hard failure.
DECODE_CATEGORIES = {
    "InvalidUtf8",
    "MissingSeparatorSpace",
    "LossyScalar",
    "DuplicateKey",
    "KeyPathConflict",
    "EmptyKey",
    "InvalidKey",
    "UnclosedCompound",
    "UnbalancedBracket",
    "MissingSeparator",
    "UnterminatedInlineCompound",
    "UnterminatedQuotedKey",
    "MalformedInlineCompound",
    "BadEscapeSequence",
    "OrphanLineAfterTopLevelInline",
}


class BlockCore:
    """Reject native and third-party imports before module execution."""

    def find_spec(self, fullname: str, path: object = None, target: object = None) -> object:
        """Отклонить native и сторонние модули до их исполнения."""
        if fullname == "ktav._core":
            raise ImportError(f"{fullname} blocked by installed pure consumer check")
        if fullname == "ktav" or fullname.startswith("ktav."):
            return None
        if not is_stdlib(fullname):
            raise ModuleNotFoundError(
                f"third-party import {fullname!r} denied in pure consumer", name=fullname
            )
        return None

    def find_module(self, fullname: str, path: object = None) -> object:
        """Пропустить устаревший протокол загрузки."""
        return None


def is_stdlib(name: str) -> bool:
    """Classify by resolved origin, without invoking import hooks recursively."""
    root = name.partition(".")[0]
    if root in sys.builtin_module_names or FrozenImporter.find_spec(root) is not None:
        return True
    spec = PathFinder.find_spec(root, sys.path)
    origin = getattr(spec, "origin", None)
    if origin in {"built-in", "frozen"}:
        return True
    if origin is None:
        return False
    resolved = Path(origin).resolve()
    is_site = any(base == resolved or base in resolved.parents for base in SITE_PATHS)
    in_stdlib = any(base == resolved or base in resolved.parents for base in STDLIB_PATHS)
    in_shared = any(
        base is not None and (resolved == base or base in resolved.parents)
        for base in (EXTENSION_PATH, WINDOWS_EXTENSION_PATH)
    )
    return (in_stdlib or in_shared) and not is_site


def install_runtime_guards() -> None:
    """Deny process/network APIs and audit events during consumer checks."""
    import builtins
    import socket
    import subprocess
    import sys

    def blocked(*args: object, **kwargs: object) -> object:
        raise AssertionError("pure consumer attempted network or subprocess use")

    socket.create_connection = blocked  # type: ignore[assignment]
    socket.socket = blocked  # type: ignore[assignment,misc]
    subprocess.Popen = blocked  # type: ignore[assignment,misc]
    builtins.__import__ = guarded_import

    def audit(event: str, args: tuple[object, ...]) -> None:
        if event.startswith(("socket.", "subprocess.")) or event in {"os.system", "os.exec"}:
            raise AssertionError(f"pure consumer audit denied {event}")

    sys.addaudithook(audit)


def guarded_import(
    name: str, globals: object = None, locals: object = None, fromlist: object = (), level: int = 0
) -> object:
    """Reject imports outside stdlib and ktav after the installed package loads."""
    if level > 0:
        return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)
    if not name:
        raise ImportError("absolute empty import is not permitted")
    if name == "ktav._core":
        raise ImportError("ktav._core blocked by installed pure consumer check")
    if name == "ktav" or name.startswith("ktav."):
        return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)
    if not is_stdlib(name):
        raise ModuleNotFoundError(f"third-party import {name!r} denied in pure consumer", name=name)
    return _ORIGINAL_IMPORT(name, globals, locals, fromlist, level)


_ORIGINAL_IMPORT = (
    __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
)


def fail(message: str) -> None:
    """Abort the check with a non-zero exit status."""
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def fixture_text(path: Path) -> str:
    r"""Byte-exact fixture text: read_bytes() then decode, never read_text.

    ``Path.read_text`` uses universal-newline mode, so a lone CR or CRLF
    in a fixture would be silently rewritten to ``\n`` before the parser
    or a canonical-byte comparison sees it. The original bytes are part
    of the test surface (§ 3.1/3.2).
    """
    return path.read_bytes().decode("utf-8")


def check_manifest(spec_tests: Path, manifest: object) -> None:
    """Spec § 8.5 manifest discipline, all violations hard failures."""
    if not isinstance(manifest, dict):
        fail("manifest.json is not an object")
    if manifest.get("schema_version") != 1:
        fail(f"unknown manifest schema_version {manifest.get('schema_version')!r}")
    categories = manifest.get("categories")
    if not isinstance(categories, dict) or set(categories) != set(INVENTORY):
        fail(f"manifest categories != the closed five-name set: {categories!r}")
    on_disk = {path.name for path in spec_tests.iterdir() if path.is_dir()}
    if on_disk != set(INVENTORY):
        fail(f"category directories on disk {sorted(on_disk)} != the closed five-name set")
    for name, count in INVENTORY.items():
        if categories[name].get("count") != count:
            fail(f"manifest count for {name} changed: {categories[name].get('count')}")
    expected_flags = {
        "invalid_utf8/lone_continuation_byte",
        "invalid_utf8/multibyte_crlf_lone_continuation",
        "invalid_utf8/bom_lone_cr_bad_byte",
        "invalid_utf8/truncated_sequence_at_eof",
        "invalid_utf8/interrupted_sequence",
        "invalid_utf8/overlong_two_byte",
        "invalid_utf8/surrogate_encoded",
        "invalid_utf8/above_max_code_point",
        "invalid_utf8/grammar_error_before_bad_byte",
    }
    flags = manifest.get("fixture_flags")
    n_flags = len(flags) if isinstance(flags, list) else -1
    if n_flags != 9:
        fail(f"fixture_flags must be exactly 9 entries, got {n_flags}")
    seen = set()
    for entry in flags:
        if not isinstance(entry, dict) or not {"category", "fixture", "flags"} <= set(entry):
            fail(f"malformed fixture_flags entry: {entry!r}")
        if entry["category"] != "invalid":
            fail(f"unknown flag category {entry['category']!r}")
        if entry["fixture"] not in expected_flags or entry["fixture"] in seen:
            fail(f"unknown or duplicated flagged fixture {entry['fixture']!r}")
        seen.add(entry["fixture"])
        if entry["flags"] != ["raw_bytes"]:
            fail(f"unknown flag set {entry['flags']!r} on {entry['fixture']!r}")
        if not (spec_tests / "invalid" / (entry["fixture"] + ".ktav")).exists():
            fail(f"flagged fixture missing on disk: {entry['fixture']}")
    if seen != expected_flags:
        fail(f"fixture_flags incomplete: missing {sorted(expected_flags - seen)}")


def expect_encode_refusal(
    dump: object, value: object, reason: str, label: object, exc_type: type
) -> None:
    """The writer ``dump`` must refuse ``value`` citing ``reason``."""
    try:
        dump(value)
    except exc_type as error:
        if reason not in str(error):
            fail(f"{label}: reason {error.message!r} lacks pinned reason {reason!r}")
    else:
        fail(f"pure accepted unrepresentable value: {label}")


def main() -> None:
    """Run every category; any mismatch, short count, or native leak fails."""
    sys.meta_path.insert(0, BlockCore())
    install_runtime_guards()

    spec_tests = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "spec" / "versions" / "0.8" / "tests"
    )
    if not spec_tests.is_dir():
        fail(f"spec corpus missing ({spec_tests}) — populate the submodule")

    import ktav
    import ktav.pure as ktav_pure

    package_path = Path(ktav.__file__).resolve()
    expected_package_dirs = {base / "ktav" for base in SITE_PATHS}
    if package_path.parent not in expected_package_dirs:
        fail(f"ktav was not imported from the active venv site-packages: {package_path}")
    if package_path == REPO / "python" / "ktav" / "__init__.py":
        fail(f"ktav import leaked from the source checkout: {package_path}")

    if getattr(ktav, "_HAS_CORE", None) is not False:
        fail("scenario violated: ktav imported with a usable native backend")
    if hasattr(ktav, "_core"):
        fail("scenario violated: ktav._core is importable")

    if ktav_pure.__spec_version__ != "0.8.1":
        fail(f"unexpected pure spec version {ktav_pure.__spec_version__!r}")

    valid_dir = spec_tests / "valid"
    manifest = json.loads((spec_tests / "manifest.json").read_text(encoding="utf-8"))
    check_manifest(spec_tests, manifest)

    # -- valid: parse, oracle, canonical bytes, round trip, format ----------
    n_valid = 0
    for ktav_file in sorted(valid_dir.rglob("*.ktav")):
        if ktav_file.name.endswith(".canonical.ktav"):
            continue
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            fail(f"valid fixture without oracle json: {ktav_file}")
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        text = fixture_text(ktav_file)
        value = ktav_pure.loads(text)
        if value != oracle:
            fail(f"pure parse mismatch: {ktav_file}")
        if ktav_pure.loads(ktav_pure.dumps(value)) != oracle:
            fail(f"pure round trip mismatch: {ktav_file}")
        canonical_file = ktav_file.with_name(ktav_file.name.replace(".ktav", ".canonical.ktav"))
        # The .canonical.ktav twin is REQUIRED per source file — a missing
        # companion must fail at the file, not only via the aggregate count.
        if not canonical_file.exists():
            fail(f"valid fixture without its .canonical.ktav twin: {ktav_file}")
        if ktav_pure.emit_canonical(value) != fixture_text(canonical_file):
            fail(f"pure canonical bytes differ: {ktav_file}")
        if ktav_pure.loads(ktav_pure.format(text)) != oracle:
            fail(f"pure format changed the value: {ktav_file}")
        if ktav_pure.format(ktav_pure.format(text)) != ktav_pure.format(text):
            fail(f"pure format is not a fixed point: {ktav_file}")
        n_valid += 1
    if n_valid != INVENTORY["valid"]:
        fail(f"valid corpus: walked {n_valid}, expected {INVENTORY['valid']}")

    # -- canonical companion count must match the valid count ---------------
    n_canonical = len(list(valid_dir.rglob("*.canonical.ktav")))
    if n_canonical != INVENTORY["valid"]:
        fail(f"canonical companions: {n_canonical}, expected {INVENTORY['valid']}")

    # -- invalid: raw bytes must be rejected --------------------------------
    n_invalid = 0
    for ktav_file in sorted((spec_tests / "invalid").rglob("*.ktav")):
        # Fail closed: the .json oracle is REQUIRED, `expected_error` is a
        # REQUIRED key, and its value must be in the closed category set.
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            fail(f"invalid fixture without oracle json: {ktav_file}")
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        if "expected_error" not in oracle:
            fail(f"invalid oracle without expected_error: {json_file}")
        if oracle["expected_error"] not in DECODE_CATEGORIES:
            fail(f"unknown expected_error category {oracle['expected_error']!r}: {json_file}")
        raw = ktav_file.read_bytes()
        try:
            ktav_pure.loads(raw)
        except ktav_pure.KtavDecodeError as error:
            if error.error != oracle["expected_error"]:
                fail(f"{ktav_file}: {error.error} != {oracle['expected_error']}")
        else:
            fail(f"pure accepted an invalid fixture: {ktav_file}")
        n_invalid += 1
    if n_invalid != INVENTORY["invalid"]:
        fail(f"invalid corpus: walked {n_invalid}, expected {INVENTORY['invalid']}")

    # -- unrepresentable: writers refuse with the pinned reason --------------
    n_unrep = 0
    for json_file in sorted((spec_tests / "unrepresentable").rglob("*.json")):
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        value = _to_python(oracle["value"])
        for dump in (ktav_pure.dumps, ktav_pure.emit_canonical):
            expect_encode_refusal(
                dump, value, oracle["unrepresentable_reason"], json_file, ktav_pure.KtavEncodeError
            )
        n_unrep += 1
    if n_unrep != INVENTORY["unrepresentable"]:
        fail(f"unrepresentable corpus: walked {n_unrep}, expected {INVENTORY['unrepresentable']}")

    # -- parseable-unrepresentable -------------------------------------------
    n_punrep = 0
    punrep_dir = spec_tests / "parseable-unrepresentable"
    for ktav_file in sorted(punrep_dir.rglob("*.ktav")):
        if ktav_file.name.endswith(".canonical.ktav"):
            continue
        json_file = ktav_file.with_suffix(".json")
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        value = ktav_pure.loads(fixture_text(ktav_file))
        if value != oracle["value"]:
            fail(f"pure parse mismatch: {ktav_file}")
        for dump in (ktav_pure.dumps, ktav_pure.emit_canonical):
            expect_encode_refusal(
                dump, value, oracle["unrepresentable_reason"], ktav_file, ktav_pure.KtavEncodeError
            )
        n_punrep += 1
    if n_punrep != INVENTORY["parseable-unrepresentable"]:
        fail(f"parseable-unrepresentable: walked {n_punrep}, expected 4")

    # -- strict-lossy: exact lax value + error/body/canonical ----------------
    n_lossy = 0
    for ktav_file in sorted((spec_tests / "strict-lossy").rglob("*.ktav")):
        json_file = ktav_file.with_suffix(".json")
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        text = fixture_text(ktav_file)
        if ktav_pure.loads(text) != oracle["lax_value"]:
            fail(f"strict-lossy lax value mismatch: {ktav_file}")
        try:
            ktav_pure.loads_strict(text)
        except ktav_pure.KtavDecodeError as error:
            if error.error != oracle["expected_error"]:
                fail(f"{ktav_file}: {error.error} != {oracle['expected_error']}")
            if error.body != oracle["body"] or error.canonical != oracle["canonical"]:
                fail(f"strict-lossy payload mismatch: {ktav_file}")
        else:
            fail(f"strict mode accepted a lossy fixture: {ktav_file}")
        n_lossy += 1
    if n_lossy != INVENTORY["strict-lossy"]:
        fail(f"strict-lossy corpus: walked {n_lossy}, expected {INVENTORY['strict-lossy']}")

    print(
        "ok: installed-pure ktav passed the full corpus"
        f" (valid={n_valid}, invalid={n_invalid}, unrepresentable={n_unrep},"
        f" parseable-unrepresentable={n_punrep}, strict-lossy={n_lossy})"
    )


def _to_python(obj: object) -> object:
    """Fixture-only ``{"$float": ...}`` encoding to real non-finite floats."""
    if isinstance(obj, dict) and set(obj) == {"$float"}:
        return {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}[
            obj["$float"]
        ]
    if isinstance(obj, dict):
        return {key: _to_python(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_to_python(item) for item in obj]
    return obj


if __name__ == "__main__":
    main()

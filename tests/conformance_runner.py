"""Shared spec-corpus conformance checks, executed per backend.

``tests/test_conformance.py`` drives every check in this module once per
backend — the native ``ktav`` top-level API and the pure-Python
``ktav.pure`` module — with identical oracles (JSON files, the spec's own
``.canonical.ktav`` bytes, strict-lossy error/body/canonical payloads,
unrepresentable reason strings, raw invalid-UTF-8 fixtures fed as raw
bytes). Neither backend may see a weakened oracle.

The native parameter is included only when the compiled extension is
actually importable; the CI ``pure-mode`` job runs this same suite
without ``_core`` (and ``tests/conftest.py`` fails that job if native
presence/absence ever contradicts the advertised scenario).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

import ktav
import ktav.pure
import pytest
from ktav._pure.errors import SPEC_SECTIONS

REPO = Path(__file__).resolve().parent.parent
SPEC_VERSION = "0.9"
# Spec 0.9 runs against the versions/0.9 directory at the pinned spec
# commit a45275688557dc9ecc24a82afb491dd46e615d4d (the submodule gitlink
# is updated by the release tooling, not by hand).
SPEC_TESTS = REPO / "spec" / "versions" / SPEC_VERSION / "tests"

VALID_DIR = SPEC_TESTS / "valid"
INVALID_DIR = SPEC_TESTS / "invalid"
UNREPRESENTABLE_DIR = SPEC_TESTS / "unrepresentable"
PARSEABLE_UNREPRESENTABLE_DIR = SPEC_TESTS / "parseable-unrepresentable"
STRICT_LOSSY_DIR = SPEC_TESTS / "strict-lossy"


# Spec § 8.5 (versions/0.8/tests/manifest.json, schema_version 1) pins
# the EXACT fixture count per category precisely so a runner pointed at
# a stale or truncated corpus fails loudly instead of quietly running
# fewer cases. These are the manifest's counts; when the manifest file
# itself is present the two are cross-checked below.
INVENTORY = {
    "valid": 228,
    "invalid": 162,
    "unrepresentable": 5,
    "parseable-unrepresentable": 4,
    "strict-lossy": 13,
}


class Backend(NamedTuple):
    """One conformance participant: a module exposing the ktav API."""

    api: Any
    kind: str  # "native" | "pure"


def available_backends() -> list[Backend]:
    """Both backends, native first, native only when actually importable."""
    backends = [Backend(ktav.pure, "pure")]
    if ktav._HAS_CORE:
        backends.insert(0, Backend(ktav, "native"))
    return backends


BACKENDS: list[Any] = [pytest.param(be, id=be.kind) for be in available_backends()]


def skip_if_missing(path: Path) -> None:
    """FAIL CLOSED: a missing spec submodule is a hard failure, never a skip.

    A skipped conformance suite is indistinguishable from a green one in
    the CI summary, so a checkout where ``git submodule update --init``
    was forgotten must show up red here.
    """
    if not path.exists():
        pytest.fail(f"spec corpus missing ({path}) — run `git submodule update --init`")


def _fixture_text(path: Path) -> str:
    """Byte-exact fixture text: read_bytes() then decode, never read_text.

    ``Path.read_text`` opens with universal newlines, so a lone CR or a
    CRLF in a fixture would be silently rewritten to ``\n`` before any
    parser or byte comparison sees it. The original CR/CRLF bytes are
    part of the spec's test surface (§ 3.1/3.2), so every .ktav read
    goes through here; raw_bytes-flagged fixtures stay raw bytes.
    """
    return path.read_bytes().decode("utf-8")


def _validate_manifest_fixture_flags(manifest: Any) -> None:
    """Spec § 8.5: validate manifest['fixture_flags'] strictly.

    The closed set of ``raw_bytes`` fixtures is derived FROM DISK: every
    .ktav under ``invalid_utf8/`` and every ``utf8_*`` fixture under
    ``diagnostics09/`` is deliberately malformed UTF-8 (§ 6.15 / 0.9
    diagnostics09) and must be listed, and nothing else may be. An
    unknown category, flag, or count anywhere in the manifest is a hard
    failure.
    """
    expected_flags: list[str] = []
    for directory, prefix in (("invalid_utf8", "invalid_utf8"), ("diagnostics09", "diagnostics09")):
        base = INVALID_DIR / directory
        if not base.exists():
            continue
        for ktav_file in sorted(base.glob("*.ktav")):
            stem = ktav_file.name[: -len(".ktav")]
            if prefix == "diagnostics09" and not stem.startswith("utf8_"):
                continue
            expected_flags.append(f"{prefix}/{stem}")
    flags = manifest["fixture_flags"]
    assert isinstance(flags, list)
    seen = []
    for entry in flags:
        assert set(entry) >= {"category", "fixture", "flags"}, f"malformed flag entry: {entry}"
        assert entry["category"] == "invalid", f"unknown flag category {entry['category']!r}"
        assert entry["fixture"] in expected_flags, f"unknown flagged fixture {entry['fixture']!r}"
        assert entry["fixture"] not in seen, f"duplicated flagged fixture {entry['fixture']!r}"
        seen.append(entry["fixture"])
        assert isinstance(entry["flags"], list), f"flag set is not a list: {entry['flags']!r}"
        assert entry["flags"] == ["raw_bytes"], (
            f"unknown flag set {entry['flags']!r} on {entry['fixture']!r}"
        )
        fixture_path = INVALID_DIR / (entry["fixture"] + ".ktav")
        assert fixture_path.exists(), f"flagged fixture missing on disk: {fixture_path}"
    # The observed set must be EXACTLY the disk-derived set — no
    # duplicates (checked per entry above) and none missing.
    assert set(seen) == set(expected_flags), (
        f"fixture_flags incomplete: missing {sorted(set(expected_flags) - set(seen))}"
    )


def json_to_python_value(obj: Any) -> Any:
    """Map the fixture-only ``{"$float": ...}`` encoding to non-finite floats."""
    if isinstance(obj, dict) and set(obj) == {"$float"}:
        return {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}[
            obj["$float"]
        ]
    if isinstance(obj, dict):
        return {key: json_to_python_value(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [json_to_python_value(item) for item in obj]
    return obj


def valid_cases() -> Iterator[pytest.param]:
    if not VALID_DIR.exists():
        return
    for ktav_file in sorted(VALID_DIR.rglob("*.ktav")):
        if ktav_file.name.endswith(".canonical.ktav"):
            continue
        # Fail closed: the JSON oracle and the .canonical.ktav twin are
        # REQUIRED companions of every valid fixture. A silently skipped
        # fixture would shrink the run instead of failing it.
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            raise AssertionError(f"valid fixture without its .json oracle: {ktav_file}")
        canonical_file = ktav_file.with_name(ktav_file.name[: -len(".ktav")] + ".canonical.ktav")
        if not canonical_file.exists():
            raise AssertionError(f"valid fixture without its .canonical.ktav twin: {ktav_file}")
        yield pytest.param(
            ktav_file, json_file, id=str(ktav_file.relative_to(VALID_DIR)).replace("\\", "/")
        )


def canonical_cases() -> Iterator[pytest.param]:
    if not VALID_DIR.exists():
        return
    for canonical_file in sorted(VALID_DIR.rglob("*.canonical.ktav")):
        source_file = canonical_file.with_name(
            canonical_file.name[: -len(".canonical.ktav")] + ".ktav"
        )
        if not source_file.exists():
            continue
        yield pytest.param(
            source_file,
            canonical_file,
            id=str(source_file.relative_to(VALID_DIR)).replace("\\", "/"),
        )


def valid_ktav_files() -> Iterator[pytest.param]:
    """Single-value variant of :func:`valid_cases`: the .ktav fixture only.

    For checks that never read the JSON oracle (e.g. the formatter
    fixed-point check); valid_cases() yields pytest.param wrappers, not
    raw tuples, so a manual ``for k, _ in`` unpack crashes at import.
    """
    for case in valid_cases():
        yield pytest.param(case.values[0], id=case.id)


def invalid_cases() -> Iterator[pytest.param]:
    if not INVALID_DIR.exists():
        return
    for ktav_file in sorted(INVALID_DIR.rglob("*.ktav")):
        # Fail closed: the .json oracle is REQUIRED, `expected_error` is a
        # REQUIRED key, and its value must be one of the closed decode
        # categories (SPEC_SECTIONS keys). A missing or unknown oracle is
        # a hard collection failure, never a conditional skip.
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            raise AssertionError(f"invalid fixture without its .json oracle: {ktav_file}")
        oracle = json.loads(json_file.read_text(encoding="utf-8"))
        if "expected_error" not in oracle:
            raise AssertionError(f"invalid oracle without expected_error: {json_file}")
        if oracle["expected_error"] not in SPEC_SECTIONS:
            raise AssertionError(
                f"unknown expected_error category {oracle['expected_error']!r}: {json_file}"
            )
        yield pytest.param(ktav_file, id=str(ktav_file.relative_to(INVALID_DIR)).replace("\\", "/"))


def unrepresentable_cases() -> Iterator[pytest.param]:
    if not UNREPRESENTABLE_DIR.exists():
        return
    for json_file in sorted(UNREPRESENTABLE_DIR.rglob("*.json")):
        yield pytest.param(
            json_file, id=str(json_file.relative_to(UNREPRESENTABLE_DIR)).replace("\\", "/")
        )


def parseable_unrepresentable_cases() -> Iterator[pytest.param]:
    if not PARSEABLE_UNREPRESENTABLE_DIR.exists():
        return
    for ktav_file in sorted(PARSEABLE_UNREPRESENTABLE_DIR.rglob("*.ktav")):
        if ktav_file.name.endswith(".canonical.ktav"):
            continue
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            continue
        yield pytest.param(
            ktav_file,
            json_file,
            id=str(ktav_file.relative_to(PARSEABLE_UNREPRESENTABLE_DIR)).replace("\\", "/"),
        )


def strict_lossy_cases() -> Iterator[pytest.param]:
    if not STRICT_LOSSY_DIR.exists():
        return
    for ktav_file in sorted(STRICT_LOSSY_DIR.rglob("*.ktav")):
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            continue
        yield pytest.param(
            ktav_file, json_file, id=str(ktav_file.relative_to(STRICT_LOSSY_DIR)).replace("\\", "/")
        )


# ---------------------------------------------------------------------------
# Per-category checks (one call per backend x fixture)
# ---------------------------------------------------------------------------


def check_valid_fixture_matches_oracle(be: Backend, ktav_file: Path, json_file: Path) -> None:
    skip_if_missing(VALID_DIR)
    text = _fixture_text(ktav_file)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert be.api.loads(text) == oracle


def check_invalid_fixture_is_rejected(be: Backend, ktav_file: Path) -> None:
    skip_if_missing(INVALID_DIR)
    raw = ktav_file.read_bytes()
    # § 6.15: since 0.9 the shared byte boundary validates raw bytes
    # BEFORE any grammar processing in BOTH backends, so a malformed
    # UTF-8 tail can never lose to an earlier grammar error and both
    # raise the same structured InvalidUtf8 envelope with raw-byte
    # offsets (line_text stays None for invalid UTF-8).
    with pytest.raises(be.api.KtavDecodeError) as exc_info:
        be.api.loads(raw)
    error = exc_info.value
    # invalid_cases() guarantees the oracle and its expected_error key.
    json_file = ktav_file.with_suffix(".json")
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert error.error == oracle["expected_error"]
    assert error.span is not None
    assert error.span["end"] > error.span["start"], "span must cover the malformed bytes"
    if oracle["expected_error"] == "InvalidUtf8":
        assert error.line_text is None, "invalid UTF-8 must not fabricate line_text"


def check_invalid_fixture_expected_location(be: Backend, ktav_file: Path) -> None:
    """Spec 0.9 diagnostics: validate expected_location when pinned.

    ``expected_location`` carries ``line`` (>= 1), ``start`` (raw UTF-8
    byte offset, BOM included, EOL never normalised), and EXACTLY ONE
    of ``end`` (exact span end) or ``minimum_end`` (span end >= bound;
    e.g. UnclosedCompound spans opener..EOF where only the opener is
    deterministic). Both the category and the envelope fields are
    checked — optional metadata is never ignored.
    """
    skip_if_missing(INVALID_DIR)
    json_file = ktav_file.with_suffix(".json")
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    loc = oracle.get("expected_location")
    if loc is None:
        return
    assert loc.get("line", 0) >= 1, f"expected_location.line must be >= 1: {json_file}"
    assert "start" in loc, f"expected_location.start required: {json_file}"
    has_end = "end" in loc
    has_min = "minimum_end" in loc
    assert has_end != has_min, (
        f"expected_location must pin exactly one of end/minimum_end: {json_file}"
    )
    if has_end:
        assert loc["end"] > loc["start"], f"empty span pinned: {json_file}"
    else:
        assert loc["minimum_end"] > loc["start"], f"empty minimum span pinned: {json_file}"
    with pytest.raises(be.api.KtavDecodeError) as exc_info:
        be.api.loads(ktav_file.read_bytes())
    error = exc_info.value
    assert error.error == oracle["expected_error"]
    assert error.line == loc["line"], f"{ktav_file}: line {error.line!r} != expected {loc['line']}"
    assert error.span is not None, f"{ktav_file}: envelope must carry a span"
    assert error.span["start"] == loc["start"], (
        f"{ktav_file}: span start {error.span['start']} != expected {loc['start']}"
    )
    if has_end:
        assert error.span["end"] == loc["end"], (
            f"{ktav_file}: span end {error.span['end']} != expected {loc['end']}"
        )
    else:
        assert error.span["end"] >= loc["minimum_end"], (
            f"{ktav_file}: span end {error.span['end']} < minimum_end {loc['minimum_end']}"
        )


def check_valid_fixture_roundtrips_through_dump(
    be: Backend, ktav_file: Path, json_file: Path
) -> None:
    """Parse → dump → parse preserves the oracle."""
    skip_if_missing(VALID_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    first = be.api.loads(_fixture_text(ktav_file))
    second = be.api.loads(be.api.dumps(first))
    assert second == oracle


def check_valid_fixture_matches_canonical_form(
    be: Backend, source_file: Path, canonical_file: Path
) -> None:
    """Parse → emit_canonical is byte-identical to the fixture's canonical form.

    Every valid fixture ships a ``.canonical.ktav`` companion holding the one
    spelling a conforming canonical writer must produce (§ 5.9.10, § 5.9.8).
    This is the only check that compares the canonical writer against the
    spec's own bytes rather than against a model of it.
    """
    skip_if_missing(VALID_DIR)
    parsed = be.api.loads(_fixture_text(source_file))
    assert be.api.emit_canonical(parsed) == canonical_file.read_bytes().decode("utf-8")


def check_unrepresentable_fixture_is_refused(be: Backend, json_file: Path) -> None:
    """Spec § 5.9.0: a writer MUST refuse every unrepresentable Value."""
    skip_if_missing(UNREPRESENTABLE_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    value = json_to_python_value(oracle["value"])
    reason = oracle["unrepresentable_reason"]
    for dump in (be.api.dumps, be.api.emit_canonical):
        with pytest.raises(be.api.KtavEncodeError) as exc_info:
            dump(value)
        assert reason in str(exc_info.value)


def check_parseable_unrepresentable_fixture_is_refused(
    be: Backend, ktav_file: Path, json_file: Path
) -> None:
    """Spec § 5.9.0: parseable-but-unwritable values must be refused by writers."""
    skip_if_missing(PARSEABLE_UNREPRESENTABLE_DIR)
    text = _fixture_text(ktav_file)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    reason = oracle["unrepresentable_reason"]
    parsed = be.api.loads(text)
    assert parsed == oracle["value"]
    for dump in (be.api.dumps, be.api.emit_canonical):
        with pytest.raises(be.api.KtavEncodeError) as exc_info:
            dump(parsed)
        assert reason in str(exc_info.value)


def check_strict_lossy_fixture_matches_oracle(
    be: Backend, ktav_file: Path, json_file: Path
) -> None:
    skip_if_missing(STRICT_LOSSY_DIR)
    text = _fixture_text(ktav_file)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert be.api.loads(text) == oracle["lax_value"]
    with pytest.raises(be.api.KtavDecodeError) as exc_info:
        be.api.loads_strict(text)
    error = exc_info.value
    assert error.error == oracle["expected_error"]
    assert error.body == oracle["body"]
    assert error.canonical == oracle["canonical"]


def check_valid_fixture_formatted_is_a_fixed_point(be: Backend, ktav_file: Path) -> None:
    """format(format(x)) == format(x) for every corpus fixture (§ 8.5 discipline)."""
    skip_if_missing(VALID_DIR)
    text = _fixture_text(ktav_file)
    once = be.api.format(text)
    assert be.api.format(once) == once


def check_valid_fixture_format_preserves_the_parsed_value(
    be: Backend, ktav_file: Path, json_file: Path
) -> None:
    """Formatting must not change the document's parsed value."""
    skip_if_missing(VALID_DIR)
    text = _fixture_text(ktav_file)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert be.api.loads(be.api.format(text)) == oracle


def check_corpus_inventory_matches_spec_8_5_manifest() -> None:
    """Guard against a silently smaller run.

    Each category above is parametrized from a directory walk, so a missing
    or renamed directory yields zero parameters and the whole category
    vanishes without a single failure. That is not hypothetical: before the
    0.7 sync this runner pointed at ``versions/0.6`` and quietly exercised
    the wrong corpus. Spec § 8.5 (new in v0.7.1) pins the exact per-category
    fixture counts in ``tests/manifest.json`` for the same reason; we
    require the manifest and assert the on-disk counts exactly, so a stale
    or truncated corpus is a red test rather than a smaller number nobody
    reads. Backend-independent — the corpus is shared by both backends.
    """
    skip_if_missing(SPEC_TESTS)
    manifest_path = SPEC_TESTS / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert set(manifest["categories"]) == set(INVENTORY)
    assert {path.name for path in SPEC_TESTS.iterdir() if path.is_dir()} == set(INVENTORY)
    for name, count in INVENTORY.items():
        assert manifest["categories"][name]["count"] == count, f"manifest count for {name} changed"
    _validate_manifest_fixture_flags(manifest)
    assert len(list(valid_cases())) == INVENTORY["valid"]
    assert len(list(canonical_cases())) == INVENTORY["valid"]
    assert len(list(invalid_cases())) == INVENTORY["invalid"]
    assert len(list(unrepresentable_cases())) == INVENTORY["unrepresentable"]
    assert len(list(parseable_unrepresentable_cases())) == INVENTORY["parseable-unrepresentable"]
    assert len(list(strict_lossy_cases())) == INVENTORY["strict-lossy"]

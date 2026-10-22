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

REPO = Path(__file__).resolve().parent.parent
SPEC_VERSION = "0.8"
# Spec 0.8.1 is published as the versions/0.8 directory at spec pin
# 388982118c0d8f767bf283356ac9c9bb50fdc3f5 — there is no separate
# versions/0.8.1 directory, so the tests run against versions/0.8.
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
    "invalid": 90,
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
        pytest.fail(
            f"spec corpus missing ({path}) — run `git submodule update --init`"
        )


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

    Exactly the 9 known entries, all category 'invalid', every flag from
    the closed {'raw_bytes'} set, and every flagged fixture present on
    disk. An unknown category, flag, or count anywhere in the manifest
    is a hard failure.
    """
    EXPECTED_FLAGS = [
        "invalid_utf8/lone_continuation_byte",
        "invalid_utf8/multibyte_crlf_lone_continuation",
        "invalid_utf8/bom_lone_cr_bad_byte",
        "invalid_utf8/truncated_sequence_at_eof",
        "invalid_utf8/interrupted_sequence",
        "invalid_utf8/overlong_two_byte",
        "invalid_utf8/surrogate_encoded",
        "invalid_utf8/above_max_code_point",
        "invalid_utf8/grammar_error_before_bad_byte",
    ]
    flags = manifest["fixture_flags"]
    assert isinstance(flags, list)
    assert len(flags) == 9, f"expected exactly 9 fixture_flags entries, got {len(flags)}"
    for entry in flags:
        assert set(entry) >= {"category", "fixture", "flags"}, f"malformed flag entry: {entry}"
        assert entry["category"] == "invalid", f"unknown flag category {entry['category']!r}"
        assert entry["fixture"] in EXPECTED_FLAGS, f"unknown flagged fixture {entry['fixture']!r}"
        assert isinstance(entry["flags"], list) and entry["flags"] == ["raw_bytes"], (
            f"unknown flag set {entry['flags']!r} on {entry['fixture']!r}"
        )
        fixture_path = INVALID_DIR / (entry["fixture"] + ".ktav")
        assert fixture_path.exists(), f"flagged fixture missing on disk: {fixture_path}"


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
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            continue
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


def invalid_cases() -> Iterator[pytest.param]:
    if not INVALID_DIR.exists():
        return
    for ktav_file in sorted(INVALID_DIR.rglob("*.ktav")):
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
    # § 6.15 InvalidUtf8 fixtures are rejected by the native wrapper's
    # UTF-8 decode (UnicodeDecodeError) but by the pure backend's own
    # pre-grammar validation (KtavDecodeError / InvalidUtf8). Both are
    # rejections; the pure backend additionally gets the § 6.15 span
    # checks below because it sees the raw bytes.
    with pytest.raises((be.api.KtavDecodeError, UnicodeDecodeError)) as exc_info:
        be.api.loads(raw)
    # When the fixture pins a category and the backend actually produced
    # an envelope (pure always does; native not for the § 6.15 fixtures,
    # which its wrapper rejects at the decode step), the category must
    # match the spec's own expectation.
    error = exc_info.value
    if isinstance(error, be.api.KtavDecodeError):
        json_file = ktav_file.with_suffix(".json")
        if json_file.exists():
            oracle = json.loads(json_file.read_text(encoding="utf-8"))
            if "expected_error" in oracle:
                assert error.error == oracle["expected_error"]
        if be.kind == "pure":
            assert error.span is not None
            assert error.span["end"] > error.span["start"], "span must cover the malformed bytes"


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

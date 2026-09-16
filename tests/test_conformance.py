"""Run the language-agnostic spec conformance suite from `ktav-lang/spec`.

The spec lives at `<repo>/spec` as a git submodule; tests skip if the
submodule isn't populated. We implement one specific spec version, so
the path is hardcoded — there is nothing to configure.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import ktav
import pytest

REPO = Path(__file__).resolve().parent.parent
SPEC_VERSION = "0.7"
SPEC_TESTS = REPO / "spec" / "versions" / SPEC_VERSION / "tests"

VALID_DIR = SPEC_TESTS / "valid"
INVALID_DIR = SPEC_TESTS / "invalid"
UNREPRESENTABLE_DIR = SPEC_TESTS / "unrepresentable"
PARSEABLE_UNREPRESENTABLE_DIR = SPEC_TESTS / "parseable-unrepresentable"


def _skip_if_missing(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"spec submodule missing ({path}) — run `git submodule update --init`")


def _json_to_python_value(obj: Any) -> Any:
    """Map the fixture-only ``{"$float": ...}`` encoding to non-finite floats."""
    if isinstance(obj, dict) and set(obj) == {"$float"}:
        return {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}[
            obj["$float"]
        ]
    if isinstance(obj, dict):
        return {key: _json_to_python_value(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_json_to_python_value(item) for item in obj]
    return obj


def _valid_cases() -> Iterator[pytest.param]:
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


def _canonical_cases() -> Iterator[pytest.param]:
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


def _invalid_cases() -> Iterator[pytest.param]:
    if not INVALID_DIR.exists():
        return
    for ktav_file in sorted(INVALID_DIR.rglob("*.ktav")):
        yield pytest.param(ktav_file, id=str(ktav_file.relative_to(INVALID_DIR)).replace("\\", "/"))


def _unrepresentable_cases() -> Iterator[pytest.param]:
    if not UNREPRESENTABLE_DIR.exists():
        return
    for json_file in sorted(UNREPRESENTABLE_DIR.rglob("*.json")):
        yield pytest.param(
            json_file, id=str(json_file.relative_to(UNREPRESENTABLE_DIR)).replace("\\", "/")
        )


def _parseable_unrepresentable_cases() -> Iterator[pytest.param]:
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


@pytest.mark.parametrize(("ktav_file", "json_file"), list(_valid_cases()))
def test_valid_fixture_matches_oracle(ktav_file: Path, json_file: Path) -> None:
    _skip_if_missing(VALID_DIR)
    text = ktav_file.read_text(encoding="utf-8")
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert ktav.loads(text) == oracle


@pytest.mark.parametrize("ktav_file", list(_invalid_cases()))
def test_invalid_fixture_is_rejected(ktav_file: Path) -> None:
    _skip_if_missing(INVALID_DIR)
    raw = ktav_file.read_bytes()
    # § 6.15 InvalidUtf8 fixtures are rejected by the wrapper's UTF-8
    # decode (UnicodeDecodeError); every other invalid fixture by the
    # Rust core (KtavDecodeError). Both are rejections.
    with pytest.raises((ktav.KtavDecodeError, UnicodeDecodeError)):
        ktav.loads(raw)


@pytest.mark.parametrize(("ktav_file", "json_file"), list(_valid_cases()))
def test_valid_fixture_roundtrips_through_dump(ktav_file: Path, json_file: Path) -> None:
    """Parse → dump → parse preserves the oracle."""
    _skip_if_missing(VALID_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    first = ktav.loads(ktav_file.read_text(encoding="utf-8"))
    second = ktav.loads(ktav.dumps(first))
    assert second == oracle


@pytest.mark.parametrize(("source_file", "canonical_file"), list(_canonical_cases()))
def test_valid_fixture_matches_canonical_form(source_file: Path, canonical_file: Path) -> None:
    """Parse → emit_canonical is byte-identical to the fixture's canonical form.

    Every valid fixture ships a ``.canonical.ktav`` companion holding the one
    spelling a conforming canonical writer must produce (§ 5.9.10, § 5.9.8).
    This is the only check that compares the canonical writer against the
    spec's own bytes rather than against a model of it.
    """
    _skip_if_missing(VALID_DIR)
    parsed = ktav.loads(source_file.read_text(encoding="utf-8"))
    assert ktav.emit_canonical(parsed) == canonical_file.read_text(encoding="utf-8")


@pytest.mark.parametrize("json_file", list(_unrepresentable_cases()))
def test_unrepresentable_fixture_is_refused(json_file: Path) -> None:
    """Spec 0.7.0 § 5.9.0: a writer MUST refuse every unrepresentable Value."""
    _skip_if_missing(UNREPRESENTABLE_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    value = _json_to_python_value(oracle["value"])
    reason = oracle["unrepresentable_reason"]
    for dump in (ktav.dumps, ktav.emit_canonical):
        with pytest.raises(ktav.KtavEncodeError) as exc_info:
            dump(value)
        assert reason in str(exc_info.value)


@pytest.mark.parametrize(("ktav_file", "json_file"), list(_parseable_unrepresentable_cases()))
def test_parseable_unrepresentable_fixture_is_refused(ktav_file: Path, json_file: Path) -> None:
    """Spec 0.7.0 § 5.9.0: parseable-but-unwritable values must be refused by writers."""
    _skip_if_missing(PARSEABLE_UNREPRESENTABLE_DIR)
    text = ktav_file.read_text(encoding="utf-8")
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    reason = oracle["unrepresentable_reason"]
    parsed = ktav.loads(text)
    assert parsed == oracle["value"]
    for dump in (ktav.dumps, ktav.emit_canonical):
        with pytest.raises(ktav.KtavEncodeError) as exc_info:
            dump(parsed)
        assert reason in str(exc_info.value)


def test_every_corpus_category_is_populated() -> None:
    """Guard against a silently empty run.

    Each category above is parametrized from a directory walk, so a missing
    or renamed directory yields zero parameters and the whole category
    vanishes without a single failure. That is not hypothetical: before the
    0.7 sync this runner pointed at ``versions/0.6`` and quietly exercised
    the wrong corpus. Assert the collection is non-empty so the failure mode
    is a red test rather than a smaller number nobody reads.
    """
    _skip_if_missing(SPEC_TESTS)
    assert len(list(_valid_cases())) > 0
    assert len(list(_canonical_cases())) > 0
    assert len(list(_invalid_cases())) > 0
    assert len(list(_unrepresentable_cases())) > 0
    assert len(list(_parseable_unrepresentable_cases())) > 0
    # Every valid fixture must ship its canonical companion.
    assert len(list(_canonical_cases())) == len(list(_valid_cases()))

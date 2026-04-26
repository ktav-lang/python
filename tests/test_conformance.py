"""Run the language-agnostic spec conformance suite from `ktav-lang/spec`.

The spec lives at `<repo>/spec` as a git submodule; tests skip if the
submodule isn't populated. We implement one specific spec version, so
the path is hardcoded — there is nothing to configure.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import ktav
import pytest


REPO = Path(__file__).resolve().parent.parent
SPEC_TESTS = REPO / "spec" / "versions" / "0.1" / "tests"

VALID_DIR = SPEC_TESTS / "valid"
INVALID_DIR = SPEC_TESTS / "invalid"


def _skip_if_missing(path: Path) -> None:
    if not path.exists():
        pytest.skip(
            f"spec submodule missing ({path}) — "
            f"run `git submodule update --init`"
        )


def _valid_cases() -> Iterator[pytest.param]:
    if not VALID_DIR.exists():
        return
    for ktav_file in sorted(VALID_DIR.rglob("*.ktav")):
        json_file = ktav_file.with_suffix(".json")
        if not json_file.exists():
            continue
        yield pytest.param(
            ktav_file, json_file, id=str(ktav_file.relative_to(VALID_DIR)).replace("\\", "/")
        )


def _invalid_cases() -> Iterator[pytest.param]:
    if not INVALID_DIR.exists():
        return
    for ktav_file in sorted(INVALID_DIR.rglob("*.ktav")):
        yield pytest.param(ktav_file, id=str(ktav_file.relative_to(INVALID_DIR)).replace("\\", "/"))


@pytest.mark.parametrize(("ktav_file", "json_file"), list(_valid_cases()))
def test_valid_fixture_matches_oracle(ktav_file: Path, json_file: Path) -> None:
    _skip_if_missing(VALID_DIR)
    text = ktav_file.read_text(encoding="utf-8")
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    assert ktav.loads(text) == oracle


@pytest.mark.parametrize("ktav_file", list(_invalid_cases()))
def test_invalid_fixture_is_rejected(ktav_file: Path) -> None:
    _skip_if_missing(INVALID_DIR)
    text = ktav_file.read_text(encoding="utf-8")
    with pytest.raises(ktav.KtavDecodeError):
        ktav.loads(text)


@pytest.mark.parametrize(("ktav_file", "json_file"), list(_valid_cases()))
def test_valid_fixture_roundtrips_through_dump(ktav_file: Path, json_file: Path) -> None:
    """Parse → dump → parse preserves the oracle."""
    _skip_if_missing(VALID_DIR)
    oracle = json.loads(json_file.read_text(encoding="utf-8"))
    first = ktav.loads(ktav_file.read_text(encoding="utf-8"))
    second = ktav.loads(ktav.dumps(first))
    assert second == oracle

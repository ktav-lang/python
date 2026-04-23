"""Run the language-agnostic spec conformance suite from `ktav-lang/spec`.

Resolution order for the spec root:
  1. ``KTAV_SPEC_DIR`` environment variable (absolute path);
  2. ``<repo>/spec`` — the git submodule ``ktav-lang/spec``;
  3. ``<repo>/../spec`` — sibling clone (local dev layout).

When none is present (e.g. a user building from a sdist with the
submodule unpopulated), the tests are skipped rather than failed.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

import ktav
import pytest


def _spec_dir() -> Path:
    env = os.environ.get("KTAV_SPEC_DIR")
    if env:
        return Path(env)
    repo = Path(__file__).resolve().parent.parent
    submodule = repo / "spec"
    if (submodule / "versions").is_dir():
        return submodule
    return repo.parent / "spec"


SPEC_DIR = _spec_dir()
VALID_DIR = SPEC_DIR / "versions" / "0.1" / "tests" / "valid"
INVALID_DIR = SPEC_DIR / "versions" / "0.1" / "tests" / "invalid"


def _skip_if_missing(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"spec fixtures not available at {path}")


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


def test_spec_dir_exists_or_env_missing() -> None:
    """Meta-check: either we can see the fixtures, or we deliberately skip.

    This lets the CI fail loud if someone removes the spec clone without
    setting ``KTAV_SPEC_DIR``; locally a missing fixture dir just skips.
    """
    env_set = os.environ.get("KTAV_SPEC_DIR") is not None
    if env_set:
        assert VALID_DIR.exists(), f"KTAV_SPEC_DIR is set but {VALID_DIR} does not exist"

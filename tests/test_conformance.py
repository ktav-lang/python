"""Run the language-agnostic spec conformance suite from `ktav-lang/spec`.

The spec lives at `<repo>/spec` as a git submodule; a missing submodule
FAILS the suite (the runner's inventory check is fail-closed — a skipped
conformance suite would look green in CI). We implement one specific
spec version, so the path is hardcoded — there is nothing to configure.

Every fixture-driven check runs SEPARATELY for each backend (native
``ktav`` top-level API and pure-Python ``ktav.pure``) with identical
oracles; the shared checks live in ``tests/conformance_runner.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import tests.conformance_runner as cr

# Backend parametrization: [(ktav, "native"), (ktav.pure, "pure")] when
# the compiled extension is importable, [pure] otherwise (the pure-mode
# CI job; tests/conftest.py keeps the two scenarios honest).
BACKENDS = cr.BACKENDS

# The fixed-point check only reads the .ktav fixture, so it parametrizes
# ONLY the ktav_file name. A decorator naming json_file here fails
# collection ("function uses no argument 'json_file'") before any test
# runs, so the pair list is projected to single-name params. When the
# corpus dir is absent valid_cases() yields nothing (the check itself
# fail-closes via skip_if_missing).
KTAV_FILES = list(cr.valid_ktav_files())


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_valid_fixture_matches_oracle(be: cr.Backend, ktav_file: Path, json_file: Path) -> None:
    cr.check_valid_fixture_matches_oracle(be, ktav_file, json_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize("ktav_file", list(cr.invalid_cases()))
def test_invalid_fixture_is_rejected(be: cr.Backend, ktav_file: Path) -> None:
    cr.check_invalid_fixture_is_rejected(be, ktav_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_valid_fixture_roundtrips_through_dump(
    be: cr.Backend, ktav_file: Path, json_file: Path
) -> None:
    cr.check_valid_fixture_roundtrips_through_dump(be, ktav_file, json_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("source_file", "canonical_file"), list(cr.canonical_cases()))
def test_valid_fixture_matches_canonical_form(
    be: cr.Backend, source_file: Path, canonical_file: Path
) -> None:
    cr.check_valid_fixture_matches_canonical_form(be, source_file, canonical_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize("json_file", list(cr.unrepresentable_cases()))
def test_unrepresentable_fixture_is_refused(be: cr.Backend, json_file: Path) -> None:
    cr.check_unrepresentable_fixture_is_refused(be, json_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.parseable_unrepresentable_cases()))
def test_parseable_unrepresentable_fixture_is_refused(
    be: cr.Backend, ktav_file: Path, json_file: Path
) -> None:
    cr.check_parseable_unrepresentable_fixture_is_refused(be, ktav_file, json_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.strict_lossy_cases()))
def test_strict_lossy_fixture_matches_oracle(
    be: cr.Backend, ktav_file: Path, json_file: Path
) -> None:
    cr.check_strict_lossy_fixture_matches_oracle(be, ktav_file, json_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize("ktav_file", KTAV_FILES)
def test_valid_fixture_formatted_is_a_fixed_point(be: cr.Backend, ktav_file: Path) -> None:
    cr.check_valid_fixture_formatted_is_a_fixed_point(be, ktav_file)


@pytest.mark.parametrize("be", BACKENDS)
@pytest.mark.parametrize(("ktav_file", "json_file"), list(cr.valid_cases()))
def test_valid_fixture_format_preserves_the_parsed_value(
    be: cr.Backend, ktav_file: Path, json_file: Path
) -> None:
    cr.check_valid_fixture_format_preserves_the_parsed_value(be, ktav_file, json_file)


def test_corpus_inventory_matches_spec_8_5_manifest() -> None:
    cr.check_corpus_inventory_matches_spec_8_5_manifest()

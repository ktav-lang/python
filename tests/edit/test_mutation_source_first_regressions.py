"""Source-first validation precedence for all public mutation APIs."""

from __future__ import annotations

from typing import Any

import pytest

from tests.edit._backends import edit_apis

APIS = edit_apis()
BROKEN = "a: {"


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("insert_value", (BROKEN, "a..b", None)),
        ("insert_value_segments", (BROKEN, None, None)),
        ("remove_value", (BROKEN, "a..b")),
        ("remove_value_segments", (BROKEN, None)),
        ("rename_key", (BROKEN, "a..b", None)),
        ("rename_key_segments", (BROKEN, None, None)),
        ("insert_value", (BROKEN, None, None)),
        ("remove_value", (BROKEN, None)),
        ("rename_key", (BROKEN, None, None)),
        ("insert_value_segments", (BROKEN, [None], None)),
        ("remove_value_segments", (BROKEN, [None])),
        ("rename_key_segments", (BROKEN, [None], "b")),
        ("rename_key_segments", (BROKEN, ["a"], None)),
    ],
)
def test_malformed_source_precedes_mutation_argument_validation(
    api: Any, name: str, args: tuple[Any, ...]
) -> None:
    with pytest.raises(api.KtavDecodeError) as caught:
        getattr(api, name)(*args)
    assert caught.value.error == "UnclosedCompound"


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("insert_value_segments", ("a: 1\n", [None], 2)),
        ("remove_value_segments", ("a: 1\n", [None])),
        ("rename_key_segments", ("a: 1\n", [None], "b")),
        ("rename_key", ("a: 1\n", "a", None)),
        ("rename_key_segments", ("a: 1\n", ["a"], None)),
    ],
)
def test_valid_source_reaches_segment_and_new_key_validation(
    api: Any, name: str, args: tuple[Any, ...]
) -> None:
    with pytest.raises((api.KtavEditError, TypeError, ValueError)):
        getattr(api, name)(*args)


class RaisingIterator:
    def __iter__(self):
        raise RuntimeError("segments iterated")


@pytest.mark.parametrize("api", APIS)
@pytest.mark.parametrize(
    ("name", "args"),
    [
        ("insert_value_segments", (BROKEN, 2)),
        ("remove_value_segments", (BROKEN,)),
        ("rename_key_segments", (BROKEN, "new")),
    ],
)
def test_malformed_source_precedes_segments_iterator(
    api: Any, name: str, args: tuple[Any, ...]
) -> None:
    with pytest.raises(api.KtavDecodeError) as caught:
        getattr(api, name)(args[0], RaisingIterator(), *args[1:])
    assert caught.value.error == "UnclosedCompound"


@pytest.mark.parametrize("api", APIS)
def test_valid_source_does_iterate_segments(api: Any) -> None:
    with pytest.raises(RuntimeError, match="segments iterated"):
        api.remove_value_segments("a: 1\n", RaisingIterator())

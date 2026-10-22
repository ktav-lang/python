"""i64 Integer-domain bounds for the pure backend (and cross-backend).

The Integer domain is exactly i64 (Rust ``try_parse_integer`` returns
``Option<i64>``; overflow → ``None`` → String per § 5.2 rule 13, with
the decimal→float fallback still available to the caller). Huge digit
runs must parse via a bounded accumulator — never ``int()`` on a
5000-digit string, which would trip CPython's ``int_max_str_digits``.
"""

from __future__ import annotations

from typing import Any

import pytest
from ktav import pure

import tests.conformance_runner as cr

I64_MIN = -9223372036854775808
I64_MAX = 9223372036854775807
NINES_5000 = "9" * 5000


@pytest.mark.parametrize("be", cr.BACKENDS)
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param("k: -9223372036854775808\n", I64_MIN, id="i64-min"),
        pytest.param("k: 9223372036854775807\n", I64_MAX, id="i64-max"),
        pytest.param("k: -9223372036854775809\n", "-9223372036854775809", id="i64-min-1"),
        pytest.param("k: 9223372036854775808\n", "9223372036854775808", id="i64-max+1"),
        pytest.param("k: 0x7fffffffffffffff\n", I64_MAX, id="hex-max"),
        pytest.param("k: -0x8000000000000000\n", I64_MIN, id="hex-min"),
        pytest.param("k: 0xffffffffffffffff\n", "0xffffffffffffffff", id="hex-overflow"),
        pytest.param(
            "k: 0o777777777777777777777\n", I64_MAX, id="oct-max"
        ),  # 21 octal 7s = 63 one-bits
        pytest.param("k: -0o1000000000000000000000\n", I64_MIN, id="oct-min"),
        pytest.param(
            "k: 0o1000000000000000000001\n", "0o1000000000000000000001", id="oct-overflow"
        ),
        pytest.param("k: " + "0b" + "1" * 63 + "\n", I64_MAX, id="bin-max"),
        pytest.param("k: -0b1" + "0" * 63 + "\n", I64_MIN, id="bin-min"),
        pytest.param("k: 0b1" + "0" * 63 + "\n", "0b1" + "0" * 63, id="bin-overflow"),
        pytest.param("k: 1_000\n", 1000, id="underscore-decimal"),
        pytest.param("k: 0xFF_FF\n", 65535, id="underscore-hex"),
        pytest.param("k: _100\n", "_100", id="leading-underscore"),
        pytest.param("k: 100_\n", "100_", id="trailing-underscore"),
        pytest.param("k: 1__0\n", "1__0", id="double-underscore"),
    ],
)
def test_integer_domain_bounds(be: cr.Backend, source: str, expected: Any) -> None:
    assert be.api.loads(source) == {"k": expected}
    assert be.api.loads(be.api.dumps({"k": expected})) == {"k": expected}


@pytest.mark.parametrize("be", cr.BACKENDS)
def test_huge_digit_run_is_string_not_error(be: cr.Backend) -> None:
    """5000 nines overflow i64 → String per § 5.2, never an int() error."""
    source = "k: " + NINES_5000 + "\n"
    # independent oracle — not derived from either backend
    assert be.api.loads(source) == {"k": NINES_5000}
    # String classification is lossless, so strict mode must not raise.
    assert be.api.loads_strict(source) == {"k": NINES_5000}


@pytest.mark.parametrize("be", cr.BACKENDS)
def test_leading_zeros_are_free(be: cr.Backend) -> None:
    """A long zero run must not act as a length cutoff: 0x000…01 → 1."""
    source = "k: 0x" + "0" * 5000 + "1\n"
    # independent oracle — not derived from either backend
    assert be.api.loads(source) == {"k": 1}


def test_writer_forces_raw_marker_for_digit_string() -> None:
    """A digit-leading String must carry the ``::`` raw marker and round-trip."""
    out = pure.dumps({"s": NINES_5000})
    # independent oracle — not derived from either backend
    assert ":: " + NINES_5000 in out
    assert pure.loads(out) == {"s": NINES_5000}


def test_canonical_emit_of_overflow_string_round_trips() -> None:
    source = "k: " + NINES_5000 + "\n"
    # independent oracle — not derived from either backend
    expected = "k:: " + NINES_5000 + "\n"
    assert pure.emit_canonical(pure.loads(source)) == expected
    assert pure.loads(expected) == {"k": NINES_5000}

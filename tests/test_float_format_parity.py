"""Verify the binding's ``format_float`` (src/lib.rs) agrees with the Rust
core 0.7.0 canonical float writer (``canonical_float``, ``Cow<'_, str>``).

For a Python float ``v``:

- ``ktav.dumps({"f": v})`` renders the binding-formatted literal
  (``format_float``: ryu's shortest text with a decimal point inserted into
  the mantissa where the grammar needs one).
- ``ktav.emit_canonical({"f": v})`` renders the crate-canonical literal.
  ``ktav`` 0.7.0 ``canonical_float`` (render/canonical.rs) applied to the
  stored text: zero or ``1e-2 <= abs < 1e7`` passes the text through
  byte-identical (``Cow::Borrowed``); anything else is rewritten to
  shortest scientific form derived from the value (``Cow::Owned``).

The canonical expectation is therefore modelled per VALUE region, with the
shortest digits taken from ``repr(v)`` (Python's shortest round-trip form —
the same digits ryu produces) and the exponent from
``Decimal(repr(abs(v))).normalize().adjusted()``.
"""

from __future__ import annotations

import random
from decimal import Decimal

import ktav
import pytest


def _literal(document: str) -> str:
    """Strip the ``f: `` prefix and trailing newline from a document."""
    assert document.startswith("f: ")
    assert document.endswith("\n")
    return document[len("f: ") : -len("\n")]


def _expected_canonical(v: float, dumps_literal: str) -> str:
    """Model of the 0.7.0 core's ``canonical_float`` applied to the
    binding's ``format_float`` output."""
    if v == 0.0 or 1e-2 <= abs(v) < 1e7:
        return dumps_literal  # Cow::Borrowed — byte-identical pass-through
    digits = "".join(map(str, Decimal(repr(abs(v))).normalize().as_tuple().digits))
    mantissa = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    sign = "-" if v < 0 else ""
    return f"{sign}{mantissa}e{Decimal(repr(abs(v))).normalize().adjusted()}"


def _assert_float_parity(v: float) -> None:
    a = _literal(ktav.dumps({"f": v}))
    b = _literal(ktav.emit_canonical({"f": v}))

    # Both texts round-trip to the same double.
    assert float(a) == v
    assert float(b) == v

    # Canonical output is exactly the core's canonical_float applied to
    # the binding's text: byte-identical in the decimal region (and for
    # zeros), rewritten shortest-scientific outside it.
    assert b == _expected_canonical(v, a)

    # The dumps document round-trips through loads.
    assert ktav.loads(ktav.dumps({"f": v}))["f"] == v


@pytest.mark.parametrize(
    ("v", "v_id"),
    [
        (0.0, "zero"),
        (-0.0, "neg-zero"),
        (1.0, "one"),
        (-1.0, "neg-one"),
        (0.5, "half"),
        (0.1, "tenth"),
        (1e-2, "boundary-decimal-1e-2"),
        (0.01, "point-zero-one"),
        (9.999999e-3, "just-below-1e-2"),
        (1e7, "boundary-scientific-1e7"),
        (9999999.0, "just-below-1e7"),
        (9999999.999999998, "just-below-1e7-precise"),
        (16777216.0, "f32-pow2"),
        (16777217.0, "f32-overflow"),
        (9007199254740993.0, "2pow53-plus-1"),
        (1e100, "1e100"),
        (1e-100, "1e-100"),
        (5e-324, "f64-min-subnormal"),
        (2.5e-324, "f64-min-subnormal-halfway"),
        (1.401298464324817e-45, "f32-min-subnormal"),
        (1.1754943508222875e-38, "f32-min-normal"),
        (3.4028234663852886e38, "f32-max"),
        (2.2250738585072014e-308, "f64-min-normal"),
        (1.7976931348623157e308, "f64-max"),
        (-1.7976931348623157e308, "f64-min"),
        (123456.789, "typical-decimal"),
        (1e-5, "small-scientific"),
        (2.5e-10, "small-scientific-2"),
    ],
)
def test_float_format_parity(v: float, v_id: str) -> None:
    _assert_float_parity(v)


@pytest.mark.parametrize(
    "v",
    [0.0, -0.0, 0.01, 1e-2, 0.5, 1.0, 123456.789, 9999999.0, 9999999.999999998],
)
def test_decimal_region_is_byte_identical(v: float) -> None:
    assert _literal(ktav.dumps({"f": v})) == _literal(ktav.emit_canonical({"f": v}))


def test_float_format_parity_random_sweep() -> None:
    """Deterministic sweep with the same assertions; failures collected."""
    rng = random.Random(20260916)
    failures: list[tuple[str, float, AssertionError]] = []
    for label, lo, hi in (
        ("wide", -1e8, 1e8),
        ("narrow", -1.0, 1.0),
    ):
        for i in range(256):
            v = rng.uniform(lo, hi)
            try:
                _assert_float_parity(v)
            except AssertionError as exc:  # pragma: no cover - only on failure
                failures.append((f"{label}-{i}", v, exc))
    assert not failures, failures


def test_canonical_zeros_exact() -> None:
    # Spec 0.7.0 § 5.9.8: zeros stay 0.0 / -0.0.
    assert ktav.emit_canonical({"z": 0.0, "nz": -0.0}) == "z: 0.0\nnz: -0.0\n"


def test_canonical_extremes_exact() -> None:
    # Pinned byte forms matching the Rust core's own unit tests.
    assert (
        ktav.emit_canonical({"k": 2.2250738585072014e-308, "mn": 5e-324})
        == "k: 2.2250738585072014e-308\nmn: 5e-324\n"
    )


def test_f32_representable_values_keep_f64_identity() -> None:
    # 16777217 is NOT f32-representable: an f32 cast or f32 normalisation
    # would collapse it to 16777216 (canonical 1.6777216e7). ryu's own
    # shortest text stays plain decimal here; the f32-collapse check is
    # that neither writer ever produces the collapsed value.
    assert ktav.dumps({"f": 16777217.0}) == "f: 16777217.0\n"
    assert ktav.emit_canonical({"f": 16777217.0}) == "f: 1.6777217e7\n"
    assert ktav.emit_canonical({"f": 16777216.0}) == "f: 1.6777216e7\n"

"""§ 3.6 number literals — classification, parsing, and canonical form.

Integers are arbitrary-precision (the native binding round-trips
bigints, so the pure backend matches it, including the documented
wider-domain exemption over the i64-only corpus oracles). Floats are
binary64 via Python's correctly-rounded ``float()`` (roundTiesToEven),
matching Rust's ``f64::from_str``.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "canonical_float",
    "canonical_int",
    "has_redundant_leading_zero",
    "is_float_literal",
    "is_integer_grammar",
    "parse_float_literal",
    "parse_integer_literal",
]


def _scan_dec_part(s: str, i: int) -> tuple[int, bool]:
    """One-or-more decimal digits with single underscores between them."""
    n = len(s)
    if i >= n or not s[i].isdigit() or not s[i].isascii():
        return i, False
    i += 1
    prev_us = False
    while i < n:
        c = s[i]
        if c == "_":
            if prev_us:
                return i, False
            prev_us = True
            i += 1
            continue
        if c.isdigit() and c.isascii():
            prev_us = False
            i += 1
            continue
        break
    if prev_us:
        return i, False
    return i, True


def _scan_exponent(s: str, i: int) -> tuple[int, bool]:
    if i >= len(s) or s[i] not in "eE":
        return i, False
    i += 1
    if i < len(s) and s[i] in "+-":
        i += 1
    return _scan_dec_part(s, i)


def is_float_literal(s: str) -> bool:
    """The § 3.6 float grammar (syntactic match, domain-independent)."""
    if not s:
        return False
    if not (s[0].isdigit() and s[0].isascii()) and s[0] not in "+-":
        return False
    if "." not in s and "e" not in s and "E" not in s:
        return False
    i = 1 if s[0] in "+-" else 0
    i, ok = _scan_dec_part(s, i)
    if not ok:
        return False
    if i < len(s) and s[i] == ".":
        i, ok = _scan_dec_part(s, i + 1)
        if not ok:
            return False
        if i < len(s) and s[i] in "eE":
            i, ok = _scan_exponent(s, i)
            if not ok:
                return False
        return i == len(s)
    if i < len(s) and s[i] in "eE":
        i, ok = _scan_exponent(s, i)
        if not ok:
            return False
        return i == len(s)
    return False


def has_redundant_leading_zero(s: str) -> bool:
    """§ 5.2: a base-10 digit run starting with ``0`` plus another digit.

    (or underscore), sign allowed — never an Integer/Float.
    """
    start = 1 if s[:1] in ("+", "-") else 0
    if len(s) <= start or s[start] != "0":
        return False
    nxt = s[start + 1] if start + 1 < len(s) else ""
    return (nxt.isdigit() and nxt.isascii()) or nxt == "_"


def _digit_value(c: str) -> int | None:
    if "0" <= c <= "9":
        return ord(c) - 48
    if "a" <= c <= "f":
        return ord(c) - 87
    if "A" <= c <= "F":
        return ord(c) - 55
    return None


_I64_MIN = -(2**63)
_I64_MAX = 2**63 - 1


def parse_integer_literal(s: str) -> int | None:
    """Parse a § 3.6 integer literal; ``None`` when it does not match.

    The value is arbitrary precision (the declared Integer domain of
    this implementation). Base prefixes are lowercase only — ``0X1A``
    falls through (pinned in 0.8.1) — and underscores are allowed only
    between consecutive digits.
    """
    if not s:
        return None
    i = 0
    negative = False
    if s[0] == "-":
        negative = True
        i = 1
    elif s[0] == "+":
        i = 1
    if i >= len(s):
        return None
    if s[i] == "0" and i + 1 < len(s):
        base_prefix = s[i + 1]
        if base_prefix == "x":
            return _parse_prefixed(s, i + 2, 16, negative)
        if base_prefix == "o":
            return _parse_prefixed(s, i + 2, 8, negative)
        if base_prefix == "b":
            return _parse_prefixed(s, i + 2, 2, negative)
    # Decimal
    digits: list[Any] = []
    prev_us = False
    count = 0
    while i < len(s):
        c = s[i]
        if c == "_":
            if prev_us or count == 0:
                return None
            prev_us = True
            i += 1
            continue
        if not (c.isdigit() and c.isascii()):
            return None
        digits.append(c)
        prev_us = False
        count += 1
        i += 1
    if prev_us or count == 0:
        return None
    value = int("".join(digits))
    if negative:
        value = -value
    # The declared Integer domain matches the Rust core's (i64): an
    # out-of-range literal falls through to String per § 5.2 rule 13.
    if not _I64_MIN <= value <= _I64_MAX:
        return None
    return value


def _parse_prefixed(s: str, i: int, radix: int, negative: bool) -> int | None:
    if i >= len(s):
        return None
    digits: list[Any] = []
    prev_us = False
    first = True
    while i < len(s):
        c = s[i]
        if c == "_":
            if prev_us or first:
                return None
            prev_us = True
            i += 1
            continue
        v = _digit_value(c)
        if v is None or v >= radix:
            return None
        digits.append(c)
        prev_us = False
        first = False
        i += 1
    if prev_us or first:
        return None
    value = int("".join(digits), radix)
    if negative:
        value = -value
    if not _I64_MIN <= value <= _I64_MAX:
        return None
    return value


def is_integer_grammar(s: str) -> bool:
    """The § 3.6 integer grammar, syntactically and domain-independently.

    (used by the writer to decide when a String needs ``::``).
    """
    if not s:
        return False
    i = 1 if s[0] in "+-" else 0
    if i >= len(s):
        return False
    if s[i] == "0" and i + 1 < len(s):
        if s[i + 1] == "x":
            return _check_prefixed(s, i + 2, 16)
        if s[i + 1] == "o":
            return _check_prefixed(s, i + 2, 8)
        if s[i + 1] == "b":
            return _check_prefixed(s, i + 2, 2)
    return _check_decimal(s, i)


def _check_decimal(s: str, i: int) -> bool:
    if i >= len(s) or not (s[i].isdigit() and s[i].isascii()):
        return False
    prev_us = False
    i += 1
    while i < len(s):
        c = s[i]
        if c == "_":
            if prev_us:
                return False
            prev_us = True
        elif c.isdigit() and c.isascii():
            prev_us = False
        else:
            return False
        i += 1
    return not prev_us


def _check_prefixed(s: str, i: int, radix: int) -> bool:
    if i >= len(s):
        return False
    first_digit = _digit_value(s[i])
    if first_digit is None or first_digit >= radix:
        return False
    prev_us = False
    i += 1
    while i < len(s):
        c = s[i]
        if c == "_":
            if prev_us:
                return False
            prev_us = True
        else:
            v = _digit_value(c)
            if v is None or v >= radix:
                return False
            prev_us = False
        i += 1
    return not prev_us


def canonical_int(value: int) -> str:
    """§ 5.9.8 Integer canonical form: base-10, ``-0`` → ``0``."""
    return str(value)


def parse_float_literal(s: str) -> float | None:
    """Parse a grammar-validated float literal to binary64.

    ``None`` when the value is non-finite on the binary64 domain
    (overflow → String per § 5.2 rule 14). Underflow to ±0.0 is an
    ordinary Float.
    """
    try:
        val = float(s.replace("_", ""))
    except ValueError:
        return None
    if val != val or val in (float("inf"), float("-inf")):
        return None
    return val


def canonical_float(value: float) -> str:
    """§ 5.9.8 Float canonical form for a finite binary64 value.

    Python's ``repr`` yields the shortest decimal that round-trips
    under roundTiesToEven — the same shortest-candidate selection the
    spec's `(s, D, k)` rule mandates for binary64 — so the digits are
    taken from ``repr`` and re-rendered per the § 5.9.8 thresholds:
    scientific when ``0 < abs < 1e-2`` or ``abs >= 1e7``, decimal form
    (mandatory decimal point) otherwise.
    """
    if value == 0.0:
        return "-0.0" if _is_negative_zero(value) else "0.0"
    digits, k = _shortest_digits(value)
    n = len(digits)
    p = n + k
    negative = value < 0.0 or _is_negative_zero(value)
    sign = "-" if negative else ""
    absval = abs(value)
    if absval < 1e-2 or absval >= 1e7:
        exp = k + n - 1
        mantissa = digits[0] + ("." + digits[1:] if n > 1 else "")
        return f"{sign}{mantissa}e{exp}"
    if p <= 0:
        body = "0." + "0" * (-p) + digits
    elif p >= n:
        body = digits + "0" * (p - n) + ".0"
    else:
        body = digits[:p] + "." + digits[p:]
    return sign + body


def _is_negative_zero(value: float) -> bool:
    return value == 0.0 and str(value)[0] == "-"


def _shortest_digits(value: float) -> tuple[str, int]:
    """``(D, k)`` with ``value == int(D) * 10**k``, ``D`` shortest with.

    nonzero first/last digits.
    """
    r = repr(value)
    if "e" in r or "E" in r:
        mantissa, _, exp_s = r.replace("E", "e").partition("e")
        exp = int(exp_s)
    else:
        mantissa, exp = r, 0
    neg = mantissa.startswith("-")
    if neg:
        mantissa = mantissa[1:]
    if "." in mantissa:
        int_part, frac_part = mantissa.split(".")
    else:
        int_part, frac_part = mantissa, ""
    digits = (int_part + frac_part).lstrip("0")
    k = exp - len(frac_part)
    # Strip trailing zeros (repr is already shortest, but be exact).
    stripped = digits.rstrip("0")
    if stripped:
        k += len(digits) - len(stripped)
        digits = stripped
    if not digits:
        digits, k = "0", 0
    if neg:
        # Sign is handled by the caller; digits stay unsigned.
        pass
    return digits, k

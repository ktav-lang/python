"""Tests for :func:`ktav.dumps_force_strings` — coerce all scalars to String.

Compounds preserve their structure; only leaf scalars (`int`, `float`,
`bool`, `None`) are flattened to their textual form and emitted via the
raw `::` marker so the output round-trips back as the same string
scalars.
"""

import ktav
import pytest


def test_int_coerced_to_string():
    # Spec 0.5.0: bare `8080` is inferred as Integer, so the force-strings
    # renderer must emit `::` to keep the value a String on round-trip.
    out = ktav.dumps_force_strings({"port": 8080})
    assert ktav.loads(out) == {"port": "8080"}


def test_float_coerced_to_string():
    # Same: bare `0.5` is inferred as Float; `::` preserves the String.
    out = ktav.dumps_force_strings({"ratio": 0.5})
    assert ktav.loads(out) == {"ratio": "0.5"}


def test_bool_coerced_to_string():
    out = ktav.dumps_force_strings({"a": True, "b": False})
    assert out == "a:: true\nb:: false\n"


def test_none_coerced_to_string():
    out = ktav.dumps_force_strings({"x": None})
    assert out == "x:: null\n"


def test_existing_string_is_unchanged_in_value():
    # The String value itself remains a String — it just becomes raw
    # so it can hold keyword-like text without being re-classified.
    parsed = ktav.loads(ktav.dumps_force_strings({"name": "hello"}))
    assert parsed == {"name": "hello"}


def test_compounds_preserved():
    obj = {"srv": {"host": "a.example", "port": 80}, "tags": [1, "x", True]}
    out = ktav.dumps_force_strings(obj)
    parsed = ktav.loads(out)
    assert parsed == {
        "srv": {"host": "a.example", "port": "80"},
        "tags": ["1", "x", "true"],
    }


def test_idempotent_after_one_pass():
    obj = {"port": 8080, "ratio": 0.5, "nested": {"flag": True, "n": None}}
    once = ktav.dumps_force_strings(obj)
    twice = ktav.dumps_force_strings(ktav.loads(once))
    assert once == twice


def test_top_level_list_force_strings():
    out = ktav.dumps_force_strings([1, True, None, "x"])
    assert ktav.loads(out) == ["1", "true", "null", "x"]


def test_top_level_scalar_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps_force_strings("hello")


def test_nan_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps_force_strings({"v": float("nan")})


def test_unsupported_type_rejected():
    class Custom:
        pass

    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps_force_strings({"v": Custom()})

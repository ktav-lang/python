"""Serializer behaviour — :func:`ktav.dumps`."""

import ktav
import pytest


def test_empty_dict_is_empty_string():
    assert ktav.dumps({}) == ""


def test_simple_string_pair():
    assert ktav.dumps({"name": "hello"}) == "name: hello\n"


def test_int_uses_integer_marker():
    assert ktav.dumps({"port": 8080}) == "port:i 8080\n"


def test_float_uses_float_marker():
    assert ktav.dumps({"ratio": 0.5}) == "ratio:f 0.5\n"


def test_float_always_has_decimal_point():
    # The parser requires a `.` in the mantissa. Make sure the serializer
    # emits it even for integer-valued floats.
    out = ktav.dumps({"x": 1e100})
    assert "." in out.split(" ", 1)[1]


def test_bool_and_null_keywords():
    out = ktav.dumps({"a": True, "b": False, "c": None})
    assert out == "a: true\nb: false\nc: null\n"


def test_string_that_looks_like_keyword_gets_raw_marker():
    # Without `::` the parser would interpret "true" as a bool.
    assert ktav.dumps({"x": "true"}) == "x:: true\n"


def test_string_starting_with_bracket_gets_raw_marker():
    # Without `::` the parser would think the value opens an array.
    out = ktav.dumps({"pattern": "[a-z]+"})
    assert out == "pattern:: [a-z]+\n"


def test_tuple_becomes_array():
    assert ktav.loads(ktav.dumps({"items": (1, 2, 3)})) == {"items": [1, 2, 3]}


def test_dict_preserves_insertion_order():
    out = ktav.dumps({"z": 1, "a": 2, "m": 3})
    assert out == "z:i 1\na:i 2\nm:i 3\n"


def test_bigint_roundtrips():
    big = 10**40
    assert ktav.loads(ktav.dumps({"n": big})) == {"n": big}


def test_top_level_list_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps([1, 2, 3])


def test_top_level_scalar_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps("hello")


def test_nan_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps({"v": float("nan")})


def test_infinity_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps({"v": float("inf")})


def test_negative_infinity_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps({"v": float("-inf")})


def test_unsupported_type_rejected():
    class Custom:
        pass

    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps({"v": Custom()})


def test_non_string_key_rejected():
    with pytest.raises(ktav.KtavEncodeError):
        ktav.dumps({42: "x"})


def test_nested_dict():
    obj = {"srv": {"host": "a.example", "port": 80}}
    assert ktav.loads(ktav.dumps(obj)) == obj


def test_bool_before_int_in_encoding():
    # bool is a subclass of int in Python; the serializer must not
    # silently encode True as `:i 1`.
    assert ktav.dumps({"x": True}) == "x: true\n"

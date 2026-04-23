"""Round-trip: ``loads(dumps(x)) == x``."""

import ktav
import pytest


@pytest.mark.parametrize(
    "obj",
    [
        {},
        {"a": "b"},
        {"port": 8080},
        {"ratio": 3.14, "on": True},
        {"nested": {"deep": {"key": "value"}}},
        {"list": [1, 2, 3]},
        {"mixed": [{"a": 1}, {"b": 2}]},
        {"many": [None, True, False, 1, 2.5, "hi"]},
        {"empty_dict": {}, "empty_list": []},
        {"unicode": "日本語"},
        {"long": "x" * 1000},
        {"negatives": {"i": -42, "f": -3.14}},
        {"big_int": 10**30},
        {"keyword_strings": ["true", "false", "null"]},
        {"bracketed": ["[::1]:8080", "{var}.tpl"]},
    ],
    ids=[
        "empty",
        "simple",
        "int",
        "float_and_bool",
        "deeply_nested",
        "list_of_ints",
        "list_of_objects",
        "mixed_list",
        "empty_compounds",
        "unicode",
        "long_string",
        "negative_numbers",
        "big_integer",
        "keyword_like_strings",
        "bracket_starting_strings",
    ],
)
def test_roundtrip(obj):
    text = ktav.dumps(obj)
    assert ktav.loads(text) == obj

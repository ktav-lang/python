"""Top-level Array support — spec § 5.0.1 (added in 0.1.1).

The first content line of a document determines the root kind:
Object (the historical behaviour) or Array (new in 0.1.1). These tests
exercise the parser side; serializer-side coverage lives in
:mod:`tests.test_dumps`.
"""

import ktav


def test_bare_scalar_at_root_is_array():
    assert ktav.loads("alpha\nbeta\ngamma") == ["alpha", "beta", "gamma"]


def test_typed_integer_item_at_root_is_array():
    assert ktav.loads(":i 1\n:i 2\n:i 3") == [1, 2, 3]


def test_typed_float_item_at_root_is_array():
    assert ktav.loads(":f 0.5\n:f 1.5") == [0.5, 1.5]


def test_raw_string_item_at_root_is_array():
    assert ktav.loads(":: true\n:: 8080") == ["true", "8080"]


def test_lone_brace_at_root_opens_array_with_object_item():
    text = "{\n  host: a.example\n  port:i 80\n}\n{\n  host: b.example\n}"
    assert ktav.loads(text) == [
        {"host": "a.example", "port": 80},
        {"host": "b.example"},
    ]


def test_lone_bracket_at_root_opens_array_with_array_item():
    text = "[\n  a\n  b\n]\n[\n  c\n]"
    assert ktav.loads(text) == [["a", "b"], ["c"]]


def test_multiline_opener_at_root_is_array():
    text = "(\n  hello\n  world\n)"
    assert ktav.loads(text) == ["hello\nworld"]


def test_pair_line_at_root_remains_object():
    # Backward-compatible: existing 0.1.0 documents still parse as Object.
    assert ktav.loads("name: hello") == {"name": "hello"}


def test_comment_lines_do_not_pick_root_kind():
    # Comments / blanks are skipped; first *content* line is the scalar.
    assert ktav.loads("# header\n\nalpha\nbeta") == ["alpha", "beta"]


def test_inside_array_root_pairs_are_just_strings():
    # Inside a top-level Array a `key: value` line is a bare scalar
    # string per § 5.4 rule 11 — no implicit reclassification.
    result = ktav.loads("alpha\nhost: localhost")
    assert result == ["alpha", "host: localhost"]

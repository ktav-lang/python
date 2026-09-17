"""Top-level Array support — spec § 5.0.1.

The first content line of a document determines the root kind:
Object (a ``key: value`` line) or Array (anything else).
These tests exercise the parser side; serializer-side coverage lives in
:mod:`tests.test_dumps`.
"""

import ktav


def test_bare_scalar_at_root_is_array():
    assert ktav.loads("alpha\nbeta\ngamma") == ["alpha", "beta", "gamma"]


def test_integer_item_at_root_is_array():
    # Spec 0.5.0: bare integers are inferred, no :i marker.
    assert ktav.loads("1\n2\n3") == [1, 2, 3]


def test_float_item_at_root_is_array():
    # Spec 0.5.0: bare floats are inferred, no :f marker.
    assert ktav.loads("0.5\n1.5") == [0.5, 1.5]


def test_raw_string_item_at_root_is_array():
    assert ktav.loads(":: true\n:: 8080") == ["true", "8080"]


def test_lone_brace_at_root_opens_root_object():
    # Spec 0.5.0 rule 4: a lone `{` on the first content line opens a
    # root multi-line Object (not an Array with one Object item).
    text = "{\n  host: a.example\n  port: 80\n}"
    assert ktav.loads(text) == {"host": "a.example", "port": 80}


def test_lone_bracket_at_root_opens_root_array():
    # Spec 0.5.0 rule 5: a lone `[` on the first content line opens a
    # root multi-line Array.
    text = "[\n  a\n  b\n  c\n]"
    assert ktav.loads(text) == ["a", "b", "c"]


def test_multiline_opener_at_root_is_array():
    text = "(\n  hello\n  world\n)"
    assert ktav.loads(text) == ["hello\nworld"]


def test_pair_line_at_root_remains_object():
    # Backward-compatible: key-value lines parse as Object.
    assert ktav.loads("name: hello") == {"name": "hello"}


def test_comment_lines_do_not_pick_root_kind():
    # Comments (##) / blanks are skipped; first *content* line is the scalar.
    assert ktav.loads("## header\n\nalpha\nbeta") == ["alpha", "beta"]


def test_single_hash_is_content_not_comment():
    # Spec 0.5.0: a single `#` is content, not a comment.
    assert ktav.loads("#not-a-comment") == ["#not-a-comment"]


def test_inside_array_root_pairs_are_just_strings():
    # Inside a top-level Array a `key: value` line is a bare scalar
    # string per § 5.4 rule 11 — no implicit reclassification.
    result = ktav.loads("alpha\nhost: localhost")
    assert result == ["alpha", "host: localhost"]

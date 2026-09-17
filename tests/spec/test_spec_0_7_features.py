"""Smoke tests for spec 0.7.0 features through the public Python API.

Covers:
- Quoted key segments that are never dotted-path-split (spec 0.7.0 § 5.3.3).
- ``\\uXXXX`` unicode escapes, recognised only inside inline-compound values
  and keys, never in multi-line scalar bodies (spec 0.7.0 § 3.7.1).
- Escape recognition forcing String classification (spec 0.7.0 § 5.2,
  breaking change).

Root Array documents (spec 0.7.0 § 5.0.1) are intentionally NOT covered here:
parser-side coverage lives in ``tests/test_top_level_array.py`` and
writer-side coverage in ``tests/test_dumps.py::test_top_level_list_renders_as_bare_array``
and ``tests/test_dumps.py::test_top_level_array_roundtrips``. This is a
deliberate non-duplication.
"""

from __future__ import annotations

import ktav
import pytest


class TestQuotedKeys:
    """Quoted key segments are never dotted-path-split (§ 5.3.3)."""

    def test_quoted_key_not_split(self):
        assert ktav.loads(r'"a.b": 1') == {"a.b": 1}

    def test_nested_quoted_key(self):
        assert ktav.loads(r'a."b.c": 1') == {"a": {"b.c": 1}}

    def test_single_quoted_key(self):
        assert ktav.loads(r"'a b': 1") == {"a b": 1}

    def test_backtick_quoted_key(self):
        assert ktav.loads(r"`x y`: 2") == {"x y": 2}

    def test_escaped_own_delimiter_in_quoted_key(self):
        # ktav text is: "a\"b": 1  (backslash-escaped double quote inside
        # a double-quoted key). The Python literal below uses \\" so the
        # document really contains the two characters backslash + quote.
        assert ktav.loads('"a\\"b": 1') == {'a"b': 1}

    def test_writer_prefers_quoted_form(self):
        # § 5.9.10: prefer the quoted form over bare-with-escape for
        # structural bytes like '.'.
        assert ktav.dumps({"a.b": 1}) == '"a.b": 1\n'

    @pytest.mark.parametrize(
        "value",
        [
            {"a.b": 1},
            {"a b": "c d"},
            {"k'x": 1},
            {'say "hi"': True},
        ],
    )
    def test_quoted_key_roundtrip(self, value):
        assert ktav.loads(ktav.dumps(value)) == value


class TestUnicodeEscapes:
    """``\\uXXXX`` escapes (§ 3.7.1): inline compounds/keys only."""

    def test_basic_escape(self):
        assert ktav.loads(r"{s: \u0041bc}") == {"s": "Abc"}

    def test_surrogate_pair(self):
        assert ktav.loads(r"{s: \ud83d\ude00}") == {"s": "\U0001f600"}

    def test_lowercase_hex(self):
        assert ktav.loads(r"{s: x\u00e9}") == {"s": "x\u00e9"}

    def test_fewer_than_four_hex_digits_is_error(self):
        with pytest.raises(ktav.KtavDecodeError):
            ktav.loads(r"{s: \u041}")

    def test_lone_high_surrogate_is_error(self):
        with pytest.raises(ktav.KtavDecodeError) as exc_info:
            ktav.loads(r"{s: \ud800}")
        assert "BadEscapeSequence" in str(exc_info.value)

    def test_escape_forces_string_classification(self):
        # § 5.2 (0.7.0 breaking change): any recognised escape forces the
        # scalar to be classified as String, never Float.
        assert ktav.loads(r"{s: 1\.0}") == {"s": "1.0"}

    def test_escape_without_named_form_forces_string(self):
        # \u002e decodes to '.', but the classification rule is the same.
        assert ktav.loads(r"{s: 1\u002e0}") == {"s": "1.0"}

    def test_not_processed_in_multiline_scalar_bodies(self):
        # The six bytes stay literal in a multi-line scalar body.
        assert ktav.loads(r"s: \u0041") == {"s": r"\u0041"}
